import httpx
import uuid
import json
from typing import Optional
from app.core.config import settings
from app.core.logging import logger
from app.graph import graph_repo
from app.agents.llm_client import llm_client


class DifyClient:
    def __init__(self):
        self.base_url = settings.DIFY_BASE_URL.rstrip("/")
        self.api_key = settings.DIFY_API_KEY
        self.risk_api_key = settings.DIFY_RISK_API_KEY or settings.DIFY_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ════════════════════════════════════════════
    # 调度方案工作流（原 run_workflow，改造降级链）
    # ════════════════════════════════════════════

    async def run_dispatch_workflow(
        self,
        area_name: str,
        disaster_type: str,
        risk_level: str,
        affected_people: int,
        triples_text: str,
        input_risk_info: str,
        vision_text: Optional[str] = None,
        user_id: str = "emergency-admin",
    ) -> dict:
        """
        调用 Dify 调度方案工作流，传入Neo4j三元组数据。

        要求Dify返回JSON格式，包含：
        - 短期措施
        - 中期措施
        - 长期措施
        - 物资分配
        - 救援队伍方案
        - 避难场所方案
        - 人员疏散方案
        - 方案备注
        """
        result = await self._call_dify_dispatch_workflow(
            area_name, disaster_type, risk_level, affected_people,
            triples_text, input_risk_info, vision_text, user_id,
        )
        # 校验 Dify 返回结果是否能解析出有效方案 JSON
        raw_text = ""
        if isinstance(result.get("result"), dict):
            raw_text = result["result"].get("text", result["result"].get("output", ""))
        elif isinstance(result.get("result"), str):
            raw_text = result["result"]
        parsed = self._try_extract_plan_json(raw_text)
        if parsed is None:
            raise RuntimeError("Dify 返回结果无法解析出有效方案JSON")
        result["fallback_level"] = "none"
        return result

    async def _call_dify_dispatch_workflow(
        self, area_name, disaster_type, risk_level, affected_people,
        triples_text, input_risk_info, vision_text, user_id,
    ) -> dict:
        """调用 Dify 调度方案工作流（传入三元组）"""
        mapped_type = self.DISASTER_TYPE_MAP.get(disaster_type, "暴雨")
        mapped_severity = self.RISK_LEVEL_MAP.get(risk_level, "中等")
        event_name = f"{area_name}{disaster_type}灾害"

        # 只发送 Dify 工作流中实际配置的变量（在 .env 中注释掉则跳过）
        inputs = {}
        if settings.DIFY_INPUT_EVENT_NAME:
            inputs[settings.DIFY_INPUT_EVENT_NAME] = event_name
        if settings.DIFY_INPUT_LOCATION:
            inputs[settings.DIFY_INPUT_LOCATION] = area_name
        if settings.DIFY_INPUT_EVENT_TYPE:
            inputs[settings.DIFY_INPUT_EVENT_TYPE] = mapped_type
        if settings.DIFY_INPUT_SEVERITY:
            inputs[settings.DIFY_INPUT_SEVERITY] = mapped_severity
        if settings.DIFY_INPUT_AFFECTED_PEOPLE:
            inputs[settings.DIFY_INPUT_AFFECTED_PEOPLE] = str(affected_people)
        if settings.DIFY_INPUT_TRIPLES:
            # Dify 工作流中的 neo4j 输入框如果是短文本类型，上限通常为 256 字符
            max_triples = 250
            if len(triples_text) > max_triples:
                logger.warning(f"[Dify 调度方案工作流] 三元组文本长度 {len(triples_text)} 超过 {max_triples}，已自动截断")
                triples_text = triples_text[: max_triples - 3] + "..."
            inputs[settings.DIFY_INPUT_TRIPLES] = triples_text
        if settings.DIFY_INPUT_RISK_INFO:
            inputs[settings.DIFY_INPUT_RISK_INFO] = input_risk_info or ""
        if vision_text and settings.DIFY_INPUT_VISION_TEXT:
            inputs[settings.DIFY_INPUT_VISION_TEXT] = vision_text

        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user_id,
        }

        logger.info("=" * 60)
        logger.info("[Dify 调度方案工作流] 传入参数:")
        logger.info(f"  完整 payload: {json.dumps(payload, ensure_ascii=False, indent=2)[:2000]}")
        logger.info("=" * 60)

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/workflows/run",
                headers=self.headers,
                json=payload,
            )
            if resp.status_code >= 400:
                err_text = resp.text
                logger.error(f"[Dify 调度方案工作流] HTTP {resp.status_code}: {err_text[:2000]}")
                resp.raise_for_status()
            data = resp.json()
            logger.info(f"Dify 调度工作流调用成功: {data.get('workflow_run_id', '')}")
            return {
                "task_id": data.get("workflow_run_id", str(uuid.uuid4())),
                "status": data.get("status", "succeeded"),
                "result": self._extract_output(data),
                "raw": data,
            }

    async def _llm_generate_dispatch_plan(
        self, area_name, disaster_type, risk_level, affected_people,
        triples_text, input_risk_info,
    ) -> dict:
        """LLM (DeepSeek) 生成结构化调度方案 - 预防方案决策Agent"""
        system_prompt = """你是【预防方案决策Agent】，由deep-seek驱动。

你的任务：综合Neo4j图数据库查询的关联关系数据和RAG检索的预防知识，生成结构化预防方案。

【方案要素】
1. 短期措施（0-24小时）：紧急响应、人员疏散、资源调配
2. 中期措施（1-7天）：应急处置、医疗救助、生活保障
3. 长期措施（7天以上）：恢复重建、制度完善、能力提升
4. 资源需求清单：人力、物资、资金、设备
5. 责任分工：各部门职责与协调机制
6. 预案触发条件：分级响应标准
7. 具体内容要详尽，1000字左右

【输出格式要求】严格输出JSON，所有key均为中文：
{
  "智能体名称": "预防方案决策Agent",
  "模型": "deepseek-v4-flash",
  "输入摘要": "输入数据的简要摘要",
  "输出": {
    "事件信息": {
      "事件名称": "事件名称",
      "事件位置": "事件位置",
      "事件类型": "事件类型",
      "严重程度": "轻微/中等/严重/特大"
    },
    "方案总览": {
      "方案名称": "预防方案名称",
      "方案等级": "I级/II级/III级/IV级",
      "方案目标": "方案目标描述",
      "预计持续时间": "预计持续时间"
    },
    "短期措施": [
      {
        "措施编号": "s1",
        "措施名称": "措施名称",
        "执行时间": "0-24小时内",
        "执行部门": "执行部门",
        "具体内容": "措施具体内容",
        "优先级": "高/中/低",
        "预计效果": "预计效果描述"
      }
    ],
    "中期措施": [
      {
        "措施编号": "m1",
        "措施名称": "措施名称",
        "执行时间": "1-7天内",
        "执行部门": "执行部门",
        "具体内容": "措施具体内容",
        "优先级": "高/中/低",
        "预计效果": "预计效果描述"
      }
    ],
    "长期措施": [
      {
        "措施编号": "l1",
        "措施名称": "措施名称",
        "执行时间": "7天以上",
        "执行部门": "执行部门",
        "具体内容": "措施具体内容",
        "优先级": "高/中/低",
        "预计效果": "预计效果描述"
      }
    ],
    "方案清单": {
      "物资调度方案": [
        {
          "resourceNo": "WH-001",
          "name": "仓库名称",
          "items": [
            {"name": "救援帐篷", "allocatedQty": 50, "unit": "顶", "availableQty": 4200},
            {"name": "应急饮用水", "allocatedQty": 1000, "unit": "瓶", "availableQty": 85000},
            {"name": "救灾棉被", "allocatedQty": 100, "unit": "床", "availableQty": 6500},
            {"name": "压缩饼干", "allocatedQty": 500, "unit": "箱", "availableQty": 48000}
          ]
        }
      ],
      "救援队伍方案": [
        {
          "resourceNo": "TEAM-001",
          "name": "队伍名称",
          "dispatchSize": 480,
          "isBusy": true,
          "task": "任务内容描述，例如：立即前往灾区开展人员搜救、转移安置和秩序维护"
        }
      ],
      "避难场所方案": ["避难场所方案文字概述，备选点位、容纳规模、配套保障条件"],
      "人员疏散方案": {"routes": "疏散路线文字描述，只保留路线本身", "totalEvacuees": 50000}
    },
    "责任分工": [
      {"部门": "部门名称", "职责": "职责描述", "负责人": "负责人角色", "联系方式": "联系方式"}
    ],
    "预案触发条件": [
      {"等级": "I级", "触发条件": "触发条件描述", "响应措施": "响应措施概述"}
    ],
    "Neo4j关联分析": {
      "关联风险节点": ["关联风险列表"],
      "受影响资产": ["受影响资产列表"],
      "传播路径": "风险传播路径描述",
      "关键控制点": ["关键控制点列表"]
    },
    "置信度": 数值0-100
  },
  "元数据": {
    "数据源": ["Neo4j图数据库", "RAG知识库"],
    "决策模型": "deepseek-v4-flash预防方案生成",
    "时间戳": "处理时间戳"
  }
}

只输出JSON，不要任何额外解释文字。"""

        severity_map = {"低": "轻微", "中": "中等", "中等": "中等", "高": "严重", "极高": "特大"}
        user_prompt = f"""请基于以下信息生成应急处置预防方案：

【灾情信息】
- 区域：{area_name}
- 灾害类型：{disaster_type}
- 风险等级：{risk_level}（对应严重程度：{severity_map.get(risk_level, '中等')}）
- 受灾人数：{affected_people}
- 情报摘要：{input_risk_info}

【Neo4j资源三元组】
{triples_text}

请仔细阅读上面的Neo4j三元组数据，其中包含受灾点的关联信息（地点、灾害类型、风险等级、受灾人数）以及可用的物资仓库、救援队伍、避难场所、物资单品（救援帐篷、应急饮用水、救灾棉被、压缩饼干、生命探测仪、大型挖掘机等）等资源。

【重要约束】
1. 物资调度方案必须引用Neo4j三元组中真实存在的物资名称（如救援帐篷、应急饮用水、救灾棉被、压缩饼干、生命探测仪、大型挖掘机等），并为每个仓库生成 "items" 明细，包含 name、allocatedQty、unit、availableQty。
2. 救援队伍方案必须为每支队伍生成 "task" 字段，描述具体任务内容。
3. 避难场所方案必须遵循就近原则，优先选择距离受灾点最近的避难场所；在满足受灾群众安置需求的前提下，尽量减少避难场所数量，能用一个就不用多个。
4. 人员疏散方案只输出 {{"routes": "疏散路线文字", "totalEvacuees": 人数}}，不要集合地点、注意事项等其他字段。
5. 所有资源编号（resourceNo）和名称必须来自Neo4j三元组中的真实数据。

直接输出JSON，不要有其他说明文字，不要有Markdown代码块包裹。"""

        content = await llm_client.chat(
            system_prompt, user_prompt,
            temperature=0.3,
            max_tokens=6000,
            provider="deepseek"
        )
        return {
            "task_id": f"deepseek-dispatch-{uuid.uuid4().hex[:8]}",
            "status": "succeeded",
            "result": content,
        }

    def _fallback_dispatch_plan(
        self, area_name, disaster_type, risk_level, affected_people, triples_text,
    ) -> dict:
        """模板兜底方案"""
        fallback_json = {
            "短期措施": [
                {
                    "措施编号": "s1",
                    "措施名称": "紧急响应启动",
                    "执行时间": "0-24小时内",
                    "执行部门": "应急指挥中心",
                    "具体内容": f"立即启动{risk_level}级别应急响应，成立现场指挥部，协调各救援力量赶赴{area_name}灾区",
                    "优先级": "高",
                    "预计效果": "快速建立指挥体系，统筹救援资源"
                },
                {
                    "措施编号": "s2",
                    "措施名称": "受灾群众转移安置",
                    "执行时间": "0-24小时内",
                    "执行部门": "应急管理局、民政局",
                    "具体内容": f"组织{affected_people}名受灾群众转移至就近避难场所，发放基本生活物资",
                    "优先级": "高",
                    "预计效果": "保障群众生命安全，减少人员伤亡"
                }
            ],
            "中期措施": [
                {
                    "措施编号": "m1",
                    "措施名称": "灾情排查与评估",
                    "执行时间": "1-7天内",
                    "执行部门": "应急管理局、自然资源局",
                    "具体内容": "全面排查房屋损坏、道路中断、地质灾害隐患等情况，开展灾情评估",
                    "优先级": "中",
                    "预计效果": "掌握详细灾情，为后续救援提供依据"
                }
            ],
            "长期措施": [
                {
                    "措施编号": "l1",
                    "措施名称": "灾后恢复重建",
                    "执行时间": "7天以上",
                    "执行部门": "住建局、交通局、民政局",
                    "具体内容": "开展房屋重建、道路修复、基础设施恢复等工作，帮助群众恢复正常生产生活",
                    "优先级": "中",
                    "预计效果": "恢复灾区正常秩序，提高防灾减灾能力"
                }
            ],
            "物资分配": [],
            "救援队伍方案": [],
            "避难场所方案": [],
            "人员疏散方案": {"疏散路线": "按就近原则疏散至安全避难场所", "疏散人数": affected_people},
            "方案备注": "本方案为系统模板自动生成，请根据实际情况调整后执行。"
        }
        return {
            "task_id": f"fallback-dispatch-{uuid.uuid4().hex[:8]}",
            "status": "fallback",
            "result": json.dumps(fallback_json, ensure_ascii=False, indent=2),
        }

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
        兼容旧接口，内部调用run_dispatch_workflow
        """
        return await self.run_dispatch_workflow(
            area_name, disaster_type, risk_level, 0,
            "", input_risk_info, vision_text, user_id,
        )

    # 灾害类型映射到 Dify 工作流的 select 选项
    DISASTER_TYPE_MAP = {
        "地震": "地震", "暴雨": "暴雨", "洪涝": "洪涝", "洪水": "洪涝",
        "山洪": "山洪", "滑坡": "滑坡", "泥石流": "泥石流", "崩塌": "崩塌",
    }

    # 风险等级映射到 Dify 工作流的 severity 选项
    RISK_LEVEL_MAP = {
        "极高": "特大", "高": "严重", "中": "中等", "中等": "中等",
        "低": "轻微", "轻微": "轻微",
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

        result = await self._call_dify_risk(
            area_name, disaster_type, description, risk_features, user_id,
        )
        result["fallback_level"] = "none"
        return result

    async def _call_dify_risk(
        self, area_name, disaster_type, description, features, user_id,
    ) -> dict:
        """调用 Dify 风险评估工作流

        Dify 工作流输入参数：
        - location_name (必填): 位置名称
        - info (必填): 爬取数据/灾情描述
        - type (必填, select): 事件类型 (暴雨/洪涝/山洪/滑坡/泥石流/崩塌/地震)
        - time (必填): 时间
        - longitude (选填): 经度
        - latitude (选填): 纬度
        """
        from datetime import datetime
        mapped_type = self.DISASTER_TYPE_MAP.get(disaster_type, "暴雨")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 将 features 和 description 合并为 info
        info_text = description or ""
        if features:
            info_text += f"\n特征数据: {json.dumps(features, ensure_ascii=False)}"

        inputs = {
            "location_name": area_name,
            "info": info_text,
            "type": mapped_type,
            "time": current_time,
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
        logger.info(f"  location_name: {area_name}")
        logger.info(f"  type: {mapped_type} (原始: {disaster_type})")
        logger.info(f"  time: {current_time}")
        logger.info(f"  info: {info_text[:200]}..." if len(info_text) > 200 else f"  info: {info_text}")
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
        """LLM 风险研判（DeepSeek 兜底）"""
        system_prompt = """你是云南省自然灾害风险评估专家。根据灾情信息和环境特征，进行风险研判。

输出格式（纯文本，不要JSON）：
## 风险研判结果
- 风险等级：（低/中/高/极高）
- 风险评分：（0-100的整数）
- 紧急等级：（1-5的整数）
- 研判依据：（简要说明判断理由）

## 防范建议
（给出3-5条具体可执行的防范措施）

注意：请严格按照上述格式输出，不要添加其他内容。"""

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

        content = await llm_client.chat(
            system_prompt, user_prompt,
            temperature=0.3,
            max_tokens=1500,
            provider="deepseek"
        )
        return {
            "task_id": f"deepseek-risk-{uuid.uuid4().hex[:8]}",
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

    def _try_extract_plan_json(self, text: str) -> Optional[dict]:
        """尝试从文本中提取有效的调度方案JSON，校验是否包含必要字段。
        兼容两种格式：
        1. 旧/平格式：key直接是"短期措施"、"物资分配"等
        2. 新格式（预防方案决策Agent）：key为"输出"，内部包含"短期措施"、"方案清单"等
        返回归一化后的JSON（扁平结构，措施在顶层，方案资源也在顶层）
        """
        import re
        if not text:
            return None
        # 去除 Markdown 代码块标记
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = text.strip()
        # 找到 JSON 对象
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            return None
        json_str = json_match.group(0)
        # 清理尾逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            return None

        # 如果是新格式（包含"输出"字段），提取并归一化
        if "输出" in parsed and isinstance(parsed["输出"], dict):
            output = parsed["输出"]
            normalized = {}
            # 措施
            for k in ["短期措施", "中期措施", "长期措施"]:
                if k in output:
                    normalized[k] = output[k]
            # 方案清单：支持结构化对象或旧版文字数组
            if "方案清单" in output and isinstance(output["方案清单"], dict):
                plan_list = output["方案清单"]
                remarks_parts = []

                # 物资分配
                materials = plan_list.get("物资调度方案", [])
                if materials and isinstance(materials, list) and isinstance(materials[0], dict):
                    # 结构化对象数组
                    normalized["物资分配"] = [
                        {
                            "resourceNo": m.get("resourceNo", ""),
                            "name": m.get("name", ""),
                            "items": m.get("items", []),
                        }
                        for m in materials
                    ]
                    for m in materials:
                        items_text = "、".join(
                            f"{it.get('name','')} {it.get('allocatedQty',0)}{it.get('unit','')}"
                            for it in m.get("items", [])
                        )
                        remarks_parts.append(f"【物资调度】{m.get('name','')}({m.get('resourceNo','')}): {items_text}")
                else:
                    normalized["物资分配"] = []
                    if "物资调度方案" in plan_list:
                        remarks_parts.append("【物资调度】" + "；".join(plan_list["物资调度方案"]))

                # 救援队伍
                teams = plan_list.get("救援队伍方案", [])
                if teams and isinstance(teams, list) and isinstance(teams[0], dict):
                    normalized["救援队伍方案"] = [
                        {
                            "resourceNo": t.get("resourceNo", ""),
                            "name": t.get("name", ""),
                            "dispatchSize": t.get("dispatchSize", t.get("size", 0)),
                            "isBusy": t.get("isBusy", True),
                            "task": t.get("task", ""),
                        }
                        for t in teams
                    ]
                    for t in teams:
                        remarks_parts.append(
                            f"【救援队伍】{t.get('name','')}({t.get('resourceNo','')}) "
                            f"派遣{t.get('dispatchSize',0)}人，任务：{t.get('task','')}"
                        )
                else:
                    normalized["救援队伍方案"] = []
                    if "救援队伍方案" in plan_list:
                        remarks_parts.append("【救援队伍】" + "；".join(plan_list["救援队伍方案"]))

                # 避难场所
                normalized["避难场所方案"] = []
                if "避难场所方案" in plan_list:
                    if isinstance(plan_list["避难场所方案"], list):
                        if plan_list["避难场所方案"] and isinstance(plan_list["避难场所方案"][0], dict):
                            normalized["避难场所方案"] = plan_list["避难场所方案"]
                        else:
                            remarks_parts.append("【避难场所】" + "；".join(plan_list["避难场所方案"]))
                    else:
                        remarks_parts.append("【避难场所】" + str(plan_list["避难场所方案"]))

                # 人员疏散
                if "人员疏散方案" in plan_list:
                    evac = plan_list["人员疏散方案"]
                    if isinstance(evac, dict):
                        normalized["人员疏散方案"] = {
                            "routes": evac.get("routes", evac.get("疏散路线", "")),
                            "totalEvacuees": evac.get("totalEvacuees", evac.get("疏散人数", 0)),
                        }
                        if evac.get("routes"):
                            remarks_parts.append("【人员疏散】疏散路线：" + str(evac["routes"]))
                    elif isinstance(evac, list):
                        evac_text = "；".join(evac)
                        normalized["人员疏散方案"] = {"routes": evac_text, "totalEvacuees": 0}
                        remarks_parts.append("【人员疏散】" + evac_text)
                else:
                    normalized["人员疏散方案"] = {"routes": "", "totalEvacuees": 0}

                # 方案备注
                overview = output.get('方案总览', {})
                if overview.get('方案名称'):
                    remarks_parts.append(f"方案名称：{overview['方案名称']}")
                if overview.get('方案目标'):
                    remarks_parts.append(f"方案目标：{overview['方案目标']}")
                if "置信度" in output:
                    remarks_parts.append(f"AI置信度：{output['置信度']}%")
                normalized["方案备注"] = "\n".join(p for p in remarks_parts if p)
            else:
                # 无方案清单时设默认值
                normalized.setdefault("物资分配", [])
                normalized.setdefault("救援队伍方案", [])
                normalized.setdefault("避难场所方案", [])
                normalized.setdefault("人员疏散方案", {"routes": "", "totalEvacuees": 0})
                normalized.setdefault("方案备注", "")

            # 事件信息回填
            if "事件信息" in output:
                ei = output["事件信息"]
                normalized["_event_info"] = ei
            parsed = normalized

        # 校验是否包含至少一种措施（短期/中期/长期）
        has_measures = any(
            key in parsed for key in ["短期措施", "中期措施", "长期措施",
                                       "shortTermMeasures", "midTermMeasures", "longTermMeasures"]
        )
        if has_measures:
            return parsed
        return None


dify_client = DifyClient()
