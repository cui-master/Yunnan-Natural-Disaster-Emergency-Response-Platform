import httpx
import uuid
<<<<<<< HEAD
=======
import json
>>>>>>> feature-cui
from typing import Optional
from app.core.config import settings
from app.core.logging import logger
from app.graph import graph_repo
<<<<<<< HEAD
=======
from app.agents.llm_client import llm_client
>>>>>>> feature-cui


class DifyClient:
    def __init__(self):
        self.base_url = settings.DIFY_BASE_URL.rstrip("/")
        self.api_key = settings.DIFY_API_KEY
<<<<<<< HEAD
=======
        self.risk_api_key = settings.DIFY_RISK_API_KEY or settings.DIFY_API_KEY
>>>>>>> feature-cui
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

<<<<<<< HEAD
=======
    # ════════════════════════════════════════════
    # 调度方案工作流（原 run_workflow，改造降级链）
    # ════════════════════════════════════════════

>>>>>>> feature-cui
    async def run_workflow(
        self,
        area_name: str,
        disaster_type: str,
        risk_level: str,
        input_risk_info: str,
        vision_text: Optional[str] = None,
        user_id: str = "emergency-admin",
    ) -> dict:
        """
        调用 Dify 工作流生成应急处置方案。
        先从 Neo4j 获取调度资源数据，再一起传给 Dify。
<<<<<<< HEAD
        """
        neo4j_data = await graph_repo.get_dispatch_plan(area_name, disaster_type)

=======

        降级链：Dify 工作流 → LLM（DeepSeek/千问）→ 模板兜底
        """
        neo4j_data = await graph_repo.get_dispatch_plan(area_name, disaster_type)

        # 第 1 级：Dify 工作流
        try:
            result = await self._call_dify_workflow(
                area_name, disaster_type, risk_level,
                input_risk_info, vision_text, neo4j_data, user_id,
            )
            result["fallback_level"] = "none"
            return result
        except Exception as e:
            logger.warning(f"Dify 调度工作流失败，降级到 LLM: {e}")

        # 第 2 级：LLM 生成
        try:
            result = await self._llm_generate_plan(
                area_name, disaster_type, risk_level,
                input_risk_info, neo4j_data,
            )
            result["fallback_level"] = "llm"
            return result
        except Exception as e:
            logger.warning(f"LLM 生成方案失败，降级到模板兜底: {e}")

        # 第 3 级：模板兜底
        result = self._fallback_plan(
            area_name, disaster_type, risk_level, input_risk_info, neo4j_data,
        )
        result["fallback_level"] = "template"
        return result

    async def _call_dify_workflow(
        self, area_name, disaster_type, risk_level,
        input_risk_info, vision_text, neo4j_data, user_id,
    ) -> dict:
        """调用 Dify 调度方案工作流"""
>>>>>>> feature-cui
        inputs = {
            "input_risk_info": input_risk_info,
            "disaster_type": disaster_type,
            "area_name": area_name,
            "risk_level": risk_level,
            "vision_text": vision_text or "",
            "neo4j_resource_data": str(neo4j_data),
        }
<<<<<<< HEAD

=======
>>>>>>> feature-cui
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user_id,
        }

<<<<<<< HEAD
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/workflows/run",
                    headers=self.headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"Dify 工作流调用成功: {data.get('workflow_run_id', '')}")
                return {
                    "task_id": data.get("workflow_run_id", str(uuid.uuid4())),
                    "status": data.get("status", "succeeded"),
                    "result": self._extract_output(data),
                    "raw": data,
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Dify HTTP 错误: {e.response.status_code} - {e.response.text}")
            return self._fallback_plan(area_name, disaster_type, risk_level, input_risk_info, neo4j_data)
        except Exception as e:
            logger.error(f"Dify 调用失败: {e}")
            return self._fallback_plan(area_name, disaster_type, risk_level, input_risk_info, neo4j_data)
=======
        # ════════════════════════════════════════════
        # 打印传给 Dify 的参数（SpringBoot 调用时）
        # ════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("[Dify 调度方案工作流] 传入参数:")
        logger.info(f"  area_name: {area_name}")
        logger.info(f"  disaster_type: {disaster_type}")
        logger.info(f"  risk_level: {risk_level}")
        logger.info(f"  user_id: {user_id}")
        logger.info(f"  input_risk_info: {input_risk_info[:200]}..." if len(input_risk_info or "") > 200 else f"  input_risk_info: {input_risk_info}")
        logger.info(f"  neo4j_data: {json.dumps(neo4j_data, ensure_ascii=False, indent=2)[:500]}...")
        logger.info("完整 payload:")
        logger.info(json.dumps(payload, ensure_ascii=False, indent=2))
        logger.info("=" * 60)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/workflows/run",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Dify 工作流调用成功: {data.get('workflow_run_id', '')}")
            return {
                "task_id": data.get("workflow_run_id", str(uuid.uuid4())),
                "status": data.get("status", "succeeded"),
                "result": self._extract_output(data),
                "raw": data,
            }

    async def _llm_generate_plan(
        self, area_name, disaster_type, risk_level,
        input_risk_info, neo4j_data,
    ) -> dict:
        """LLM 生成应急处置方案（第 2 级降级）"""
        system_prompt = """你是云南省自然灾害应急决策专家。根据灾情信息和可用资源数据，生成结构化的应急处置方案。

方案必须包含以下章节：
## 一、风险研判概况
## 二、防灾物资前置调配方案
## 三、可用救援力量
## 四、避难场所安排
## 五、调度建议

要求：方案具体、可执行，结合实际资源数据。"""

        user_prompt = f"""请基于以下信息生成应急处置方案：

【灾情信息】
- 区域：{area_name}
- 灾害类型：{disaster_type}
- 风险等级：{risk_level}
- 情报摘要：{input_risk_info}

【Neo4j 可用资源数据】
物资仓库推荐：{neo4j_data.get('recommendations', [])}
可用救援队伍：{neo4j_data.get('available_teams', [])}
附近避难场所：{neo4j_data.get('shelters', [])}

请生成完整的应急处置方案。"""

        content = await llm_client.chat(system_prompt, user_prompt, max_tokens=2500)
        return {
            "task_id": f"llm-{uuid.uuid4().hex[:8]}",
            "status": "succeeded",
            "result": content,
        }

    # ════════════════════════════════════════════
    # 风险评估工作流（新增）
    # ════════════════════════════════════════════

    async def run_risk_assessment(
        self,
        area_name: str,
        disaster_type: str,
        description: str,
        features: Optional[dict] = None,
        user_id: str = "emergency-admin",
    ) -> dict:
        """
        调用 Dify 风险评估工作流，对灾情事件进行审核研判。

        降级链：Dify 风险评估 → LLM 风险研判 → 规则引擎兜底
        """
        features = features or {}
        risk_features = {
            "area_name": area_name,
            "rainfall_24h": features.get("rainfall_24h", 0),
            "rainfall_3d": features.get("rainfall_3d", 0),
            "rainfall_7d": features.get("rainfall_7d", 0),
            "geological_risk_level": features.get("geological_risk_level", "中"),
            "weather_warning": features.get("weather_warning"),
            "water_level_ratio": features.get("water_level_ratio", 0),
            "max_magnitude": features.get("max_magnitude", 0),
            "opinion_hot_count": features.get("opinion_hot_count", 0),
            "sentiment_score": features.get("sentiment_score", 0.5),
        }

        # 第 1 级：Dify 风险评估工作流
        try:
            result = await self._call_dify_risk(
                area_name, disaster_type, description, risk_features, user_id,
            )
            result["fallback_level"] = "none"
            return result
        except Exception as e:
            logger.warning(f"Dify 风险评估失败，降级到 LLM: {e}")

        # 第 2 级：LLM 风险研判
        try:
            result = await self._llm_risk_assessment(
                area_name, disaster_type, description, risk_features,
            )
            result["fallback_level"] = "llm"
            return result
        except Exception as e:
            logger.warning(f"LLM 风险研判失败，降级到规则引擎: {e}")

        # 第 3 级：规则引擎兜底
        result = self._rule_based_risk(area_name, disaster_type, risk_features)
        result["fallback_level"] = "rule"
        return result

    async def _call_dify_risk(
        self, area_name, disaster_type, description, features, user_id,
    ) -> dict:
        """调用 Dify 风险评估工作流"""
        inputs = {
            "area_name": area_name,
            "disaster_type": disaster_type,
            "description": description,
            "features": str(features),
        }
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user_id,
        }
        headers = {
            "Authorization": f"Bearer {self.risk_api_key}",
            "Content-Type": "application/json",
        }

        # ════════════════════════════════════════════
        # 打印传给 Dify 的参数（SpringBoot 调用时）
        # ════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("[Dify 风险评估工作流] 传入参数:")
        logger.info(f"  area_name: {area_name}")
        logger.info(f"  disaster_type: {disaster_type}")
        logger.info(f"  description: {description[:200]}..." if len(description or "") > 200 else f"  description: {description}")
        logger.info(f"  features: {json.dumps(features, ensure_ascii=False, indent=2)}")
        logger.info(f"  user_id: {user_id}")
        logger.info("完整 payload:")
        logger.info(json.dumps(payload, ensure_ascii=False, indent=2))
        logger.info("=" * 60)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/workflows/run",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Dify 风险评估成功: {data.get('workflow_run_id', '')}")
            return {
                "task_id": data.get("workflow_run_id", str(uuid.uuid4())),
                "status": data.get("status", "succeeded"),
                "result": self._extract_output(data),
                "raw": data,
            }

    async def _llm_risk_assessment(
        self, area_name, disaster_type, description, features,
    ) -> dict:
        """LLM 风险研判（第 2 级降级）"""
        system_prompt = """你是云南省自然灾害风险评估专家。根据灾情信息和环境特征，进行风险研判。

输出格式：
## 风险研判结果
- 风险等级：（低/中/高/极高）
- 风险评分：（0-100）
- 紧急等级：（1-5）
- 研判依据：（简要说明）

## 防范建议
（具体可执行的防范措施）"""

        user_prompt = f"""请对以下灾情进行风险研判：

【灾情信息】
- 区域：{area_name}
- 灾害类型：{disaster_type}
- 灾情描述：{description}

【环境特征】
- 24小时降雨：{features.get('rainfall_24h', 0)}mm
- 3日降雨：{features.get('rainfall_3d', 0)}mm
- 地质风险等级：{features.get('geological_risk_level', '中')}
- 气象预警：{features.get('weather_warning', '无')}
- 水位比例：{features.get('water_level_ratio', 0)}
- 最大震级：{features.get('max_magnitude', 0)}
- 舆情热度：{features.get('opinion_hot_count', 0)}

请给出风险研判结果和防范建议。"""

        content = await llm_client.chat(system_prompt, user_prompt, max_tokens=1500)
        return {
            "task_id": f"llm-risk-{uuid.uuid4().hex[:8]}",
            "status": "succeeded",
            "result": content,
        }

    def _rule_based_risk(self, area_name, disaster_type, features) -> dict:
        """规则引擎风险研判（第 3 级兜底，复用 pipeline/risk_model）"""
        try:
            from app.pipeline.risk_model import risk_model
            result = risk_model.assess(features, disaster_type)
            content = f"""## 风险研判结果（规则引擎）
- 风险等级：{result.risk_level}
- 风险评分：{result.risk_score}
- 紧急等级：{result.urgent_level}
- 模型版本：{result.model_version}

## 贡献因子
{result.contributing_factors}

说明：Dify 和 LLM 均不可用，当前为规则引擎研判结果。"""
            return {
                "task_id": f"rule-{uuid.uuid4().hex[:8]}",
                "status": "succeeded",
                "result": content,
                "risk_level": result.risk_level,
                "risk_score": result.risk_score,
            }
        except Exception as e:
            logger.error(f"规则引擎也失败: {e}")
            return {
                "task_id": f"err-{uuid.uuid4().hex[:8]}",
                "status": "failed",
                "result": f"风险研判全部失败: {e}",
            }

    # ════════════════════════════════════════════
    # 辅助方法
    # ════════════════════════════════════════════
>>>>>>> feature-cui

    def _extract_output(self, data: dict) -> str:
        if "data" in data and "outputs" in data["data"]:
            outputs = data["data"]["outputs"]
            if isinstance(outputs, dict):
                for v in outputs.values():
                    if isinstance(v, str) and len(v) > 20:
                        return v
                return str(outputs)
            return str(outputs)
        return data.get("answer", str(data))

    def _fallback_plan(
        self, area_name: str, disaster_type: str, risk_level: str,
        input_risk_info: str, neo4j_data: dict,
    ) -> dict:
<<<<<<< HEAD
        """Dify 不可用时，基于 Neo4j 数据生成保底方案"""
=======
        """模板兜底方案（第 3 级）"""
>>>>>>> feature-cui
        warehouses = neo4j_data.get("recommendations", [])
        teams = neo4j_data.get("available_teams", [])
        shelters = neo4j_data.get("shelters", [])

        warehouse_text = "\n".join(
            f"- {w.get('warehouse_name')}：{w.get('material_name')} "
            f"({w.get('stock_num', 0)}件)，距离 {w.get('total_dist', 0):.1f}km"
            for w in warehouses[:5]
        ) or "无可用物资仓库"

        team_text = "\n".join(
            f"- {t.get('team_name')}，距离 {t.get('dist', 0):.1f}km"
            for t in teams[:5]
        ) or "无可用救援队伍"

        shelter_text = "\n".join(
<<<<<<< HEAD
            f"- {s.get('name')}，剩余容量 {s.get('remain_space', 0)}人，距离 {s.get('dist', 0):.1f}km"
            for s in shelters[:5]
        ) or "无可用避难场所"

        result = f"""# 应急处置方案（自动生成-降级模式）
=======
            f"- {s.get('name')}，已容纳 {s.get('accommodated_count', 0)}/"
            f"{s.get('max_capacity', 0)}人，可用 {s.get('available_space', 0)}人，"
            f"距离 {s.get('dist', 0):.1f}km"
            for s in shelters[:5]
        ) or "无可用避难场所"

        result = f"""# 应急处置方案（模板兜底）
>>>>>>> feature-cui

## 一、风险研判概况
- 区域：{area_name}
- 灾害类型：{disaster_type}
- 风险等级：{risk_level}
- 情报摘要：{input_risk_info[:200]}

## 二、防灾物资前置调配方案
{warehouse_text}

## 三、可用救援力量
{team_text}

## 四、避难场所安排
{shelter_text}

## 五、调度依据说明
本方案依托时序风险模型研判 + Neo4j 图数据库路网资源推演生成。
<<<<<<< HEAD
Dify 工作流服务暂不可用，当前为降级输出模式。
=======
Dify 工作流和 LLM 服务均不可用，当前为模板兜底输出。
>>>>>>> feature-cui
"""
        return {
            "task_id": f"fallback-{uuid.uuid4().hex[:8]}",
            "status": "fallback",
            "result": result,
        }


dify_client = DifyClient()
