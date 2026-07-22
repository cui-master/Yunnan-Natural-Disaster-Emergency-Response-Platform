"""
云南自然灾害应急协同决策平台 — AI 服务（MVP 桩）
FastAPI 提供 /api/plan/generate，返回结构化应急处置方案。
预留 LangChain / LlamaIndex 接入点：将 build_plan() 内部替换为真实 LLM/Agent 调用即可。
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Union, List, Dict, Any
import time

app = FastAPI(title="云南应急 AI 服务 (MVP 桩)", version="0.1")

# 预案模板（真实环境由 RAG + LLM 生成）
TEMPLATES: Dict[str, List[str]] = {
    "EARTHQUAKE": [
        "立即疏散周边居民并清点人数",
        "开辟生命通道，调集搜救犬与破拆设备",
        "搭建临时医疗点与伤员分类",
        "对危房与次生灾害点设置警戒",
    ],
    "FLOOD": [
        "转移低洼地带与沿河人员",
        "加固堤防、开启排涝设备",
        "调度冲锋舟、救生衣等水域装备",
        "开放就近避难所并保障饮水食品",
    ],
    "LANDSLIDE": [
        "封锁滑坡体下游道路与区域",
        "布设监测点，预警二次滑坡",
        "转移受威胁住户",
        "抢修进出通道保障救援",
    ],
    "DEFAULT": [
        "核实灾情范围、等级与受影响人口",
        "划定警戒区并发布预警",
        "调度就近救援力量先行处置",
        "建立现场指挥与信息报送机制",
    ],
}

TYPE_LABELS = {
    "EARTHQUAKE": "地震",
    "FLOOD": "洪涝",
    "LANDSLIDE": "滑坡",
}


class PlanRequest(BaseModel):
    incidentId: Optional[Union[int, str]] = None
    title: str = ""
    type: str = ""
    level: str = ""
    description: str = ""


def build_suggestions(req: PlanRequest) -> List[Dict[str, Any]]:
    return [
        {"resourceType": "PERSONNEL", "name": "抢险队员", "suggestQty": 30},
        {"resourceType": "VEHICLE", "name": "救援卡车", "suggestQty": 5},
        {"resourceType": "MATERIAL", "name": "帐篷", "suggestQty": 50},
        {"resourceType": "SHELTER", "name": "临时避难所", "suggestQty": 1},
        {"resourceType": "VEHICLE", "name": "救护车", "suggestQty": 2},
    ]


def build_plan(req: PlanRequest) -> Dict[str, Any]:
    """预留接入点：此处替换为 LangChain/LlamaIndex 真实调用。"""
    t = (req.type or "").upper()
    steps = TEMPLATES.get(t, TEMPLATES["DEFAULT"])
    label = TYPE_LABELS.get(t, "综合")
    return {
        "title": f"【{label}】{req.title or '灾情'} 应急处置方案",
        "content": (
            "本方案由 AI Agent 基于事件特征与应急预案库生成，"
            "包含处置步骤、资源调度建议与引用来源，待应急指挥人员人工修订后审批执行。"
        ),
        "steps": steps,
        "resourceSuggestions": build_suggestions(req),
        "citations": [
            {
                "source": "《云南省自然灾害应急预案（2023 修订）》",
                "excerpt": "特别重大自然灾害由省政府启动Ⅰ级响应，设立现场指挥部……",
                "score": 0.91,
            },
            {
                "source": "历史案例：2022 年某县 5.1 级地震救援复盘",
                "excerpt": "震后 1 小时内完成首轮人员疏散，黄金 72 小时为重点……",
                "score": 0.84,
            },
        ],
    }


@app.post("/api/plan/generate")
def generate(req: PlanRequest) -> Dict[str, Any]:
    time.sleep(0.3)  # 模拟 LLM 推理时延
    return build_plan(req)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
