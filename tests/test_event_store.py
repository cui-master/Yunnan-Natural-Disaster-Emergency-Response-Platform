import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))

from app.services.event_store import EventStore
from app.models.schemas import DisasterEvent, DisasterType, SeverityLevel
from datetime import datetime, timedelta


@pytest.fixture
def store():
    return EventStore(max_events=100)


@pytest.fixture
def sample_events():
    events = []
    now = datetime.now()
    for i in range(10):
        events.append(DisasterEvent(
            id=f"event-{i}",
            disaster_type=DisasterType.EARTHQUAKE if i % 2 == 0 else DisasterType.FLOOD,
            title=f"测试事件{i}",
            location="云南省昆明市",
            severity=SeverityLevel.HIGH if i < 5 else SeverityLevel.MEDIUM,
            occurred_at=now - timedelta(hours=i),
            source="test",
        ))
    return events


class TestEventStore:
    @pytest.mark.asyncio
    async def test_add_events(self, store, sample_events):
        new_count = await store.add_events(sample_events, "test")
        assert new_count == 10

        new_count2 = await store.add_events(sample_events, "test")
        assert new_count2 == 0

    @pytest.mark.asyncio
    async def test_get_events(self, store, sample_events):
        await store.add_events(sample_events, "test")

        all_events = await store.get_events()
        assert len(all_events) == 10

        earthquake_events = await store.get_events(disaster_type="earthquake")
        assert len(earthquake_events) == 5

        flood_events = await store.get_events(disaster_type="flood")
        assert len(flood_events) == 5

        high_severity = await store.get_events(severity="high")
        assert len(high_severity) == 5

    @pytest.mark.asyncio
    async def test_get_event_by_id(self, store, sample_events):
        await store.add_events(sample_events, "test")

        event = await store.get_event_by_id("event-0")
        assert event is not None
        assert event.id == "event-0"

        event = await store.get_event_by_id("nonexistent")
        assert event is None

    @pytest.mark.asyncio
    async def test_get_stats(self, store, sample_events):
        await store.add_events(sample_events, "test")

        stats = await store.get_stats()
        assert stats["total_events"] == 10
        assert stats["by_type"]["earthquake"] == 5
        assert stats["by_type"]["flood"] == 5
        assert stats["by_severity"]["high"] == 5
        assert stats["by_severity"]["medium"] == 5

    @pytest.mark.asyncio
    async def test_max_events_limit(self):
        store = EventStore(max_events=5)
        events = []
        for i in range(10):
            events.append(DisasterEvent(
                id=f"event-{i}",
                disaster_type=DisasterType.OTHER,
                title=f"事件{i}",
                location="测试",
                severity=SeverityLevel.LOW,
                occurred_at=datetime.now(),
                source="test",
            ))

        await store.add_events(events, "test")
        all_events = await store.get_events()
        assert len(all_events) == 5
