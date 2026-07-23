import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data-pipeline"))

from app.models.schemas import DisasterEvent, DisasterType, SeverityLevel
from app.crawlers import MockCrawler


@pytest.fixture
def sample_event():
    return DisasterEvent(
        id="test-event-1",
        disaster_type=DisasterType.EARTHQUAKE,
        title="测试地震事件",
        description="这是一个测试事件",
        location="云南省昆明市",
        latitude=25.05,
        longitude=102.72,
        severity=SeverityLevel.MEDIUM,
        source="测试源",
    )


class TestDisasterEvent:
    def test_event_creation(self, sample_event):
        assert sample_event.id == "test-event-1"
        assert sample_event.disaster_type == DisasterType.EARTHQUAKE
        assert sample_event.severity == SeverityLevel.MEDIUM

    def test_event_model_dump(self, sample_event):
        data = sample_event.model_dump(mode="json")
        assert data["id"] == "test-event-1"
        assert data["disaster_type"] == "earthquake"
        assert data["severity"] == "medium"


class TestMockCrawler:
    @pytest.mark.asyncio
    async def test_mock_crawl(self):
        crawler = MockCrawler()
        result = await crawler.crawl()

        assert result.source == "模拟数据"
        assert result.total_count > 0
        assert len(result.events) == result.total_count
        assert result.error is None

    @pytest.mark.asyncio
    async def test_mock_event_fields(self):
        crawler = MockCrawler()
        result = await crawler.crawl()

        for event in result.events:
            assert event.id is not None
            assert event.disaster_type is not None
            assert event.title is not None
            assert event.location is not None
            assert event.severity is not None
            assert event.occurred_at is not None

    def test_generate_event_id(self):
        crawler = MockCrawler()
        id1 = crawler._generate_event_id("test", "key1")
        id2 = crawler._generate_event_id("test", "key1")
        id3 = crawler._generate_event_id("test", "key2")

        assert id1 == id2
        assert id1 != id3

    def test_parse_severity(self):
        crawler = MockCrawler()
        assert crawler._parse_severity("红色预警") == SeverityLevel.CRITICAL
        assert crawler._parse_severity("橙色预警") == SeverityLevel.HIGH
        assert crawler._parse_severity("黄色预警") == SeverityLevel.MEDIUM
        assert crawler._parse_severity("蓝色预警") == SeverityLevel.LOW

    def test_parse_disaster_type(self):
        crawler = MockCrawler()
        assert crawler._parse_disaster_type("发生地震") == DisasterType.EARTHQUAKE
        assert crawler._parse_disaster_type("暴雨洪涝") == DisasterType.FLOOD
        assert crawler._parse_disaster_type("山体滑坡") == DisasterType.LANDSLIDE
        assert crawler._parse_disaster_type("森林火灾") == DisasterType.FOREST_FIRE


class TestYunnanNetCrawler:
    def test_extract_location(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler

        crawler = YunnanNetCrawler(keywords=["测试"])

        assert "昆明市" in crawler._extract_location("昆明市盘龙区发生地震")
        assert "普洱市" in crawler._extract_location("普洱市墨江县发生5.0级地震")
        assert "大理州" in crawler._extract_location("大理州祥云县森林火情")
        assert "昭通市" in crawler._extract_location("昭通市彝良县遭遇暴雨")
        assert crawler._extract_location("云南省发布预警") == "云南省"
        assert crawler._extract_location("其他地方发生的事") is None

    def test_parse_severity_from_content(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler

        crawler = YunnanNetCrawler(keywords=["测试"])

        assert crawler._parse_severity_from_content("启动一级响应，特别重大灾害") == SeverityLevel.CRITICAL
        assert crawler._parse_severity_from_content("橙色预警，多人死亡") == SeverityLevel.HIGH
        assert crawler._parse_severity_from_content("黄色预警，群众受灾") == SeverityLevel.MEDIUM
        assert crawler._parse_severity_from_content("普通新闻") == SeverityLevel.LOW

    def test_extract_affected_people(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler

        crawler = YunnanNetCrawler(keywords=["测试"])

        assert crawler._extract_affected_people("转移安置群众33户94人") == 94
        assert crawler._extract_affected_people("受灾群众2300余人") == 2300
        assert crawler._extract_affected_people("紧急转移500人") == 500
        assert crawler._extract_affected_people("无人员伤亡") is None

    def test_extract_casualties(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler

        crawler = YunnanNetCrawler(keywords=["测试"])

        assert crawler._extract_casualties("造成3人死亡，5人受伤") == 8
        assert crawler._extract_casualties("2人遇难") == 2
        assert crawler._extract_casualties("未出现人员伤亡情况") is None

    def test_extract_economic_loss(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler

        crawler = YunnanNetCrawler(keywords=["测试"])

        assert crawler._extract_economic_loss("经济损失850.5万元") == 850.5
        assert crawler._extract_economic_loss("造成损失约1.2亿元") == 12000.0
        assert crawler._extract_economic_loss("没有重大损失") is None

    def test_extract_coordinates(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler

        crawler = YunnanNetCrawler(keywords=["测试"])

        lat, lon = crawler._extract_coordinates("云南省昆明市盘龙区")
        assert lat == 25.04
        assert lon == 102.72

        lat, lon = crawler._extract_coordinates("普洱市墨江县")
        assert lat == 22.82
        assert lon == 100.97

        lat, lon = crawler._extract_coordinates("不知名的地方")
        assert lat is None
        assert lon is None

    def test_parse_date(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler
        from datetime import datetime

        crawler = YunnanNetCrawler(keywords=["测试"])

        result = crawler._parse_date("2026-07-23", "")
        assert result.year == 2026
        assert result.month == 7
        assert result.day == 23

        result = crawler._parse_date("", "事故发生在2026年7月21日晚上")
        assert result.year == 2026
        assert result.month == 7
        assert result.day == 21

    def test_default_keywords(self):
        from app.crawlers.yunnan_net import YunnanNetCrawler

        crawler = YunnanNetCrawler()
        assert len(crawler.keywords) > 10
        assert any("地震" in kw for kw in crawler.keywords)
        assert any("洪水" in kw for kw in crawler.keywords)
        assert any("云南" in kw for kw in crawler.keywords)
