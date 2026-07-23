import httpx
import uuid
from typing import Optional
from app.core.config import settings
from app.core.logging import logger
from app.graph import graph_repo


class DifyClient:
    def __init__(self):
        self.base_url = settings.DIFY_BASE_URL.rstrip("/")
        self.api_key = settings.DIFY_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
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
        调用 Dify 工作流生成应急处置方案。
        先从 Neo4j 获取调度资源数据，再一起传给 Dify。
        """
        neo4j_data = await graph_repo.get_dispatch_plan(area_name, disaster_type)

        inputs = {
            "input_risk_info": input_risk_info,
            "disaster_type": disaster_type,
            "area_name": area_name,
            "risk_level": risk_level,
            "vision_text": vision_text or "",
            "neo4j_resource_data": str(neo4j_data),
        }

        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user_id,
        }

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
        """Dify 不可用时，基于 Neo4j 数据生成保底方案"""
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
            f"- {s.get('name')}，剩余容量 {s.get('remain_space', 0)}人，距离 {s.get('dist', 0):.1f}km"
            for s in shelters[:5]
        ) or "无可用避难场所"

        result = f"""# 应急处置方案（自动生成-降级模式）

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
Dify 工作流服务暂不可用，当前为降级输出模式。
"""
        return {
            "task_id": f"fallback-{uuid.uuid4().hex[:8]}",
            "status": "fallback",
            "result": result,
        }


dify_client = DifyClient()
