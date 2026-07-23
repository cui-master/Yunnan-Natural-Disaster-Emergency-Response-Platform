"""
数据管线编排器（Pipeline Orchestrator）
完整流程：
  采集 → 校验 → 多源融合 → 风险研判 → Neo4j 更新 → (可选) Dify方案生成

支持：
  - 定时调度（APScheduler）
  - 手动触发（API 调用）
  - 单区域/全区域
  - 状态跟踪与统计
"""
import time
from datetime import datetime
from typing import Optional
from app.core.logging import logger
from app.graph import graph_repo
from app.pipeline.collectors import collector_manager
from app.pipeline.validator import data_validator, fusion_engine
from app.pipeline.risk_model import risk_model
from app.pipeline.models import RiskResult


class PipelineStatus:
    """管线运行状态跟踪"""
    def __init__(self):
        self.last_run_time: Optional[datetime] = None
        self.last_run_status: str = "idle"
        self.last_run_duration: float = 0.0
        self.last_run_stats: dict = {}
        self.current_status: str = "idle"
        self.run_count: int = 0
        self.history: list[dict] = []  # 最近10次运行记录

    def to_dict(self) -> dict:
        return {
            "current_status": self.current_status,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_run_status": self.last_run_status,
            "last_run_duration_seconds": round(self.last_run_duration, 2),
            "last_run_stats": self.last_run_stats,
            "run_count": self.run_count,
        }


pipeline_status = PipelineStatus()


class DataPipeline:
    """数据管线主类"""

    # 默认监测区域（云南10个高风险区县）
    DEFAULT_AREAS = [
        "昭通市镇雄县", "昆明市东川区", "大理州漾濞县",
        "怒江州贡山县", "普洱市澜沧县", "楚雄州南华县",
        "丽江市宁蒗县", "红河州元阳县", "文山州广南县", "德宏州盈江县",
    ]

    def __init__(self):
        self.status = pipeline_status

    async def run_full_pipeline(self, area_list: Optional[list[str]] = None,
                                trigger_dify: bool = False) -> dict:
        """
        执行完整管线流程
        :param area_list: 区域列表，None 则用默认10个区县
        :param trigger_dify: 是否对高/极高风险区域触发 Dify 方案生成
        """
        if self.status.current_status == "running":
            return {"error": "管线正在运行中，请稍后再试"}

        start_time = time.time()
        self.status.current_status = "running"
        stats = {}

        try:
            areas = area_list or self.DEFAULT_AREAS
            logger.info(f"===== 数据管线启动，共 {len(areas)} 个区域 =====")

            # 1. 数据采集
            logger.info("[1/5] 数据采集中...")
            raw_data = await collector_manager.collect_all(areas)
            weather_list = raw_data.get("weather", [])
            geology_list = raw_data.get("geology", [])
            hydrology_list = raw_data.get("hydrology", [])
            opinion_list = raw_data.get("public_opinion", [])
            stats["collected"] = {
                "weather": len(weather_list),
                "geology": len(geology_list),
                "hydrology": len(hydrology_list),
                "public_opinion": len(opinion_list),
                "total": len(weather_list) + len(geology_list) + len(hydrology_list) + len(opinion_list),
            }

            # 2. 数据校验
            logger.info("[2/5] 数据校验中...")
            validated = data_validator.validate_all(
                weather_list, geology_list, hydrology_list, opinion_list
            )
            stats["validation"] = validated.get("_stats", {})

            valid_weather = validated["weather"]
            valid_geology = validated["geology"]
            valid_hydro = validated["hydrology"]
            valid_opinion = validated["public_opinion"]

            # 3. 多源数据融合
            logger.info("[3/5] 多源数据融合中...")
            fused_features = {}
            for area in areas:
                features = fusion_engine.fuse_area_data(
                    area, valid_weather, valid_geology, valid_hydro, valid_opinion
                )
                fused_features[area] = features
            stats["fused_areas"] = len(fused_features)

            # 4. 风险研判
            logger.info("[4/5] 风险研判中...")
            all_risk_results: list[RiskResult] = []
            area_highest_risk = {}

            for area, features in fused_features.items():
                area_results = risk_model.assess_area(features)
                all_risk_results.extend(area_results)

                # 取该区域最高风险等级作为整体风险
                if area_results:
                    highest = max(area_results, key=lambda r: r.risk_score)
                    area_highest_risk[area] = highest
            stats["risk_results"] = len(all_risk_results)
            stats["high_risk_areas"] = sum(
                1 for r in area_highest_risk.values()
                if r.risk_level in ["高", "极高"]
            )

            # 5. 更新 Neo4j 图谱
            logger.info("[5/5] 更新 Neo4j 风险属性...")
            updated_count = await self._sync_to_neo4j(area_highest_risk)
            stats["neo4j_updated"] = updated_count

            # 6. (可选) 触发 Dify 生成预防方案
            dify_triggered = []
            if trigger_dify:
                logger.info("[6/6] 触发 Dify 方案生成...")
                dify_triggered = await self._trigger_high_risk_dify(area_highest_risk)
                stats["dify_triggered"] = len(dify_triggered)

            # 完成
            duration = time.time() - start_time
            self.status.current_status = "idle"
            self.status.last_run_status = "success"
            self.status.last_run_time = datetime.now()
            self.status.last_run_duration = duration
            self.status.last_run_stats = stats
            self.status.run_count += 1

            # 保留历史
            self.status.history.append({
                "time": datetime.now().isoformat(),
                "status": "success",
                "duration": round(duration, 2),
                "stats": stats,
            })
            if len(self.status.history) > 10:
                self.status.history = self.status.history[-10:]

            logger.info(f"===== 数据管线完成，耗时 {duration:.2f}s =====")

            return {
                "status": "success",
                "duration_seconds": round(duration, 2),
                "stats": stats,
                "high_risk_areas": {
                    area: {
                        "risk_level": r.risk_level,
                        "risk_score": r.risk_score,
                        "disaster_type": r.disaster_type,
                        "urgent_level": r.urgent_level,
                    }
                    for area, r in area_highest_risk.items()
                    if r.risk_level in ["高", "极高"]
                },
                "dify_triggered": dify_triggered,
            }

        except Exception as e:
            duration = time.time() - start_time
            self.status.current_status = "idle"
            self.status.last_run_status = "failed"
            self.status.last_run_time = datetime.now()
            self.status.last_run_duration = duration
            self.status.last_run_stats = {"error": str(e)}
            self.status.run_count += 1

            logger.error(f"数据管线执行失败: {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "duration_seconds": round(duration, 2)}

    async def _sync_to_neo4j(self, area_highest_risk: dict[str, RiskResult]) -> int:
        """
        将风险研判结果同步到 Neo4j DisasterSpot 节点
        更新 risk_level, urgent_level, disaster_type 属性
        """
        count = 0
        spots = await graph_repo.list_high_risk_spots()
        spot_map = {s.get("name"): s.get("id") for s in spots}

        for area_name, risk_result in area_highest_risk.items():
            spot_id = spot_map.get(area_name)
            if not spot_id:
                logger.warning(f"点位 {area_name} 不在 Neo4j 中，跳过更新")
                continue
            try:
                await graph_repo.update_risk_level(
                    spot_id=spot_id,
                    risk_level=risk_result.risk_level,
                    urgent_level=risk_result.urgent_level,
                    disaster_type=[risk_result.disaster_type],
                )
                count += 1
                logger.debug(
                    f"更新 {area_name}: {risk_result.risk_level} "
                    f"(评分 {risk_result.risk_score}, 紧急度 {risk_result.urgent_level})"
                )
            except Exception as e:
                logger.error(f"更新 {area_name} 到 Neo4j 失败: {e}")

        logger.info(f"Neo4j 风险属性同步完成，更新 {count} 个点位")
        return count

    async def _trigger_high_risk_dify(self, area_highest_risk: dict[str, RiskResult]) -> list[str]:
        """
        对高风险/极高风险区域触发 Dify 生成预防方案
        返回触发成功的区域列表
        """
        triggered = []
        try:
            from app.agents import dify_client
        except ImportError:
            logger.warning("Dify 客户端不可用，跳过方案生成")
            return triggered

        for area_name, risk_result in area_highest_risk.items():
            if risk_result.risk_level not in ["高", "极高"]:
                continue
            try:
                await dify_client.run_workflow(
                    area_name=area_name,
                    disaster_type=risk_result.disaster_type,
                    risk_level=risk_result.risk_level,
                    input_risk_info=self._build_risk_info_text(risk_result),
                )
                triggered.append(area_name)
            except Exception as e:
                logger.error(f"触发 {area_name} Dify 方案失败: {e}")

        return triggered

    def _build_risk_info_text(self, risk_result: RiskResult) -> str:
        """构造风险情报文本，供 Dify 使用"""
        factors = risk_result.contributing_factors
        factor_text = "、".join(f"{k}{v}" for k, v in factors.items()) if factors else "多因素综合"
        return (
            f"【{risk_result.risk_level}风险预警】{risk_result.area_name} "
            f"{risk_result.disaster_type}风险评分 {risk_result.risk_score} 分，"
            f"紧急等级 {risk_result.urgent_level} 级。"
            f"主要贡献因子：{factor_text}。"
            f"研判模型版本：{risk_result.model_version}，"
            f"数据来源：{','.join(risk_result.data_sources) or '未知'}。"
        )

    def get_status(self) -> dict:
        return self.status.to_dict()


data_pipeline = DataPipeline()
