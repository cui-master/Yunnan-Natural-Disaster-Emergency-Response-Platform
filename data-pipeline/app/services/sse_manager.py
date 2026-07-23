import asyncio
from typing import Set
from sse_starlette.sse import EventSourceResponse
from app.models.schemas import DisasterEvent
from app.core.logging import logger
from app.core.config import settings


class SSEManager:
    """SSE 连接管理器 - 管理所有 SSE 客户端连接"""

    def __init__(self):
        self._clients: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def register(self) -> asyncio.Queue:
        """注册新客户端，返回消息队列"""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._clients.add(queue)
        logger.info(f"SSE 客户端已连接，当前连接数: {len(self._clients)}")
        return queue

    async def unregister(self, queue: asyncio.Queue):
        """注销客户端"""
        async with self._lock:
            self._clients.discard(queue)
        logger.info(f"SSE 客户端已断开，当前连接数: {len(self._clients)}")

    async def broadcast(self, event: dict, event_type: str = "message"):
        """向所有客户端广播消息"""
        async with self._lock:
            queues = list(self._clients)

        if not queues:
            return

        sse_event = {
            "event": event_type,
            "data": event,
            "retry": settings.SSE_RETRY_TIMEOUT,
        }

        disconnected = []
        for queue in queues:
            try:
                queue.put_nowait(sse_event)
            except asyncio.QueueFull:
                disconnected.append(queue)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(queue)

        if disconnected:
            async with self._lock:
                for q in disconnected:
                    self._clients.discard(q)

    async def broadcast_new_event(self, event: DisasterEvent):
        """广播新灾害事件"""
        await self.broadcast(
            event=event.model_dump(mode="json"),
            event_type="new_event",
        )

    async def broadcast_crawl_result(self, result: dict):
        """广播爬取结果"""
        await self.broadcast(
            event=result,
            event_type="crawl_result",
        )

    async def broadcast_keepalive(self):
        """广播心跳消息"""
        await self.broadcast(
            event={"status": "alive", "timestamp": asyncio.get_event_loop().time()},
            event_type="keepalive",
        )

    @property
    def client_count(self) -> int:
        return len(self._clients)


sse_manager = SSEManager()
