from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.agents import dify_client
from app.schemas import WorkflowRunRequest, WorkflowRunResponse
from app.core.logging import logger
import json

router = APIRouter(prefix="/api/v1/workflow", tags=["Dify 工作流-方案生成"])


@router.post("/run", response_model=WorkflowRunResponse, summary="调用 Dify 生成应急处置方案")
async def run_workflow(req: WorkflowRunRequest):
    """
    触发 Dify 工作流，生成完整的灾前预防或灾后救援方案。
    Dify 内部会调用 Neo4j 调度接口 + RAG 预案检索 + LLM 生成。
    """
    try:
        result = await dify_client.run_workflow(
            area_name=req.area_name,
            disaster_type=req.disaster_type,
            risk_level=req.risk_level,
            input_risk_info=req.input_risk_info,
            vision_text=req.vision_text,
        )
        return WorkflowRunResponse(
            task_id=result["task_id"],
            status=result["status"],
            result=result.get("result"),
        )
    except Exception as e:
        logger.error(f"工作流调用失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/stream", summary="流式调用 Dify 工作流（SSE）")
async def run_workflow_stream(req: WorkflowRunRequest):
    """流式输出方案内容，供前端大屏实时展示"""
    async def generate():
        result = await dify_client.run_workflow(
            area_name=req.area_name,
            disaster_type=req.disaster_type,
            risk_level=req.risk_level,
            input_risk_info=req.input_risk_info,
            vision_text=req.vision_text,
        )
        content = result.get("result", "")
        for i in range(0, len(content), 50):
            chunk = content[i:i+50]
            yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
