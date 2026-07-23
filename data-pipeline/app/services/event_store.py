from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import deque
import asyncio
from app.models.schemas import DisasterEvent, CrawlResult
from app.core.logging import logger


class EventStore:
    """内存事件存储 - 管理爬取到的灾害事件"""

    def __init__(self, max_events: int = 1000):
        self._events: Dict[str, DisasterEvent] = {}
        self._event_list: deque = deque(maxlen=max_events)
        self._last_crawl_time: Optional[datetime] = None
        self._crawl_history: deque = deque(maxlen=100)
        self._lock = asyncio.Lock()

    async def add_events(self, events: List[DisasterEvent], source: str) -> int:
        """添加新事件，返回新增数量"""
        async with self._lock:
            new_count = 0
            for event in events:
                if event.id not in self._events:
                    self._events[event.id] = event
                    self._event_list.append(event)
                    new_count += 1
                else:
                    self._events[event.id] = event

            logger.info(f"事件存储: 新增 {new_count} 条，总计 {len(self._events)} 条")
            return new_count

    async def record_crawl(self, result: CrawlResult):
        """记录爬取结果"""
        async with self._lock:
            self._last_crawl_time = result.crawled_at
            self._crawl_history.append(result)

    async def get_events(
        self,
        disaster_type: Optional[str] = None,
        severity: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 100,
        hours: Optional[int] = None,
    ) -> List[DisasterEvent]:
        """查询事件列表"""
        async with self._lock:
            events = list(self._event_list)

        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            events = [e for e in events if e.occurred_at >= cutoff]

        if disaster_type:
            events = [e for e in events if e.disaster_type.value == disaster_type]

        if severity:
            events = [e for e in events if e.severity.value == severity]

        if location:
            events = [e for e in events if location in e.location]

        events.sort(key=lambda x: x.occurred_at, reverse=True)
        return events[:limit]

    async def get_event_by_id(self, event_id: str) -> Optional[DisasterEvent]:
        """根据ID获取事件"""
        async with self._lock:
            return self._events.get(event_id)

    async def get_stats(self) -> dict:
        """获取统计信息"""
        async with self._lock:
            events = list(self._event_list)

        stats = {
            "total_events": len(self._events),
            "last_crawl_time": self._last_crawl_time.isoformat() if self._last_crawl_time else None,
            "crawl_count": len(self._crawl_history),
            "by_type": {},
            "by_severity": {},
        }

        for event in events:
            dtype = event.disaster_type.value
            stats["by_type"][dtype] = stats["by_type"].get(dtype, 0) + 1

            sev = event.severity.value
            stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1

        return stats

    async def get_crawl_history(self, limit: int = 20) -> List[dict]:
        """获取爬取历史"""
        async with self._lock:
            history = list(self._crawl_history)

        history.sort(key=lambda x: x.crawled_at, reverse=True)
        return [
            {
                "source": r.source,
                "total_count": r.total_count,
                "new_count": r.new_count,
                "error": r.error,
                "crawled_at": r.crawled_at.isoformat(),
            }
            for r in history[:limit]
        ]


event_store = EventStore()
