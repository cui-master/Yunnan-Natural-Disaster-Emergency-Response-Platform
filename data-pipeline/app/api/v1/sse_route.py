import asyncio
from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from typing import Optional
from app.services import sse_manager, event_store
from app.core.logging import logger

router = APIRouter()


@router.get("/sse")
async def sse_endpoint(request: Request):
    """
    SSE 数据流端点

    事件类型：
    - new_event: 新灾害事件
    - crawl_result: 爬取结果
    - keepalive: 心跳保活
    """
    queue = await sse_manager.register()

    async def event_generator():
        try:
            stats = await event_store.get_stats()
            yield {
                "event": "connected",
                "data": {
                    "status": "connected",
                    "client_count": sse_manager.client_count,
                    "stats": stats,
                },
                "retry": 3000,
            }

            while True:
                if await request.is_disconnected():
                    logger.info("SSE 客户端断开连接")
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield message
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            logger.info("SSE 连接被取消")
        except Exception as e:
            logger.error(f"SSE 连接异常: {e}")
        finally:
            await sse_manager.unregister(queue)

    return EventSourceResponse(
        event_generator(),
        ping=15,
        media_type="text/event-stream",
    )
