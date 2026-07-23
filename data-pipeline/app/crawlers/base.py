from typing import List, Dict, Optional
from datetime import datetime, timedelta
import hashlib
import json
from app.models.schemas import DisasterEvent, DisasterType, SeverityLevel, CrawlResult
from app.core.logging import logger


class BaseCrawler:
    """爬虫基类"""

    name: str = "base"
    source: str = "base"

    def __init__(self):
        self.session = None

    async def crawl(self) -> CrawlResult:
        """执行爬取，返回结果"""
        raise NotImplementedError

    def _generate_event_id(self, source: str, unique_key: str) -> str:
        """生成事件唯一ID"""
        raw = f"{source}:{unique_key}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _parse_severity(self, level: str) -> SeverityLevel:
        """解析严重程度"""
        level = level.lower()
        if any(k in level for k in ["特别重大", "红色", "一级", "critical", "extreme"]):
            return SeverityLevel.CRITICAL
        if any(k in level for k in ["重大", "橙色", "二级", "severe", "high"]):
            return SeverityLevel.HIGH
        if any(k in level for k in ["较大", "黄色", "三级", "moderate", "medium"]):
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    def _parse_disaster_type(self, text: str) -> DisasterType:
        """根据文本推断灾害类型"""
        text = text.lower()
        type_mapping = {
            DisasterType.EARTHQUAKE: ["地震", "earthquake", "震"],
            DisasterType.FLOOD: ["洪水", "洪涝", "暴雨", "flood", "rainstorm"],
            DisasterType.TYPHOON: ["台风", "飓风", "typhoon", "hurricane"],
            DisasterType.DROUGHT: ["干旱", "旱灾", "drought"],
            DisasterType.LANDSLIDE: ["滑坡", "泥石流", "山体滑坡", "landslide", "mudslide"],
            DisasterType.FOREST_FIRE: ["森林火灾", "山火", "林火", "forest fire", "wildfire"],
            DisasterType.STORM: ["风暴", "大风", "冰雹", "雷暴", "storm", "hail"],
        }
        for dtype, keywords in type_mapping.items():
            for kw in keywords:
                if kw in text:
                    return dtype
        return DisasterType.OTHER


class MockCrawler(BaseCrawler):
    """模拟数据爬虫 - 用于测试和演示"""

    name = "mock"
    source = "模拟数据"

    async def crawl(self) -> CrawlResult:
        """生成模拟灾害数据"""
        try:
            events: List[DisasterEvent] = []
            now = datetime.now()

            mock_events = [
                {
                    "title": "昆明市盘龙区发生3.2级地震",
                    "description": "据云南省地震台网测定，昆明市盘龙区发生3.2级地震，震源深度10千米。",
                    "location": "云南省昆明市盘龙区",
                    "latitude": 25.05,
                    "longitude": 102.72,
                    "disaster_type": DisasterType.EARTHQUAKE,
                    "severity": SeverityLevel.LOW,
                    "occurred_at": now - timedelta(minutes=15),
                    "affected_people": 0,
                    "casualties": 0,
                },
                {
                    "title": "昭通市彝良县遭遇暴雨洪涝灾害",
                    "description": "彝良县持续强降雨引发洪涝灾害，部分乡镇道路被淹，已紧急转移群众500余人。",
                    "location": "云南省昭通市彝良县",
                    "latitude": 27.64,
                    "longitude": 104.06,
                    "disaster_type": DisasterType.FLOOD,
                    "severity": SeverityLevel.HIGH,
                    "occurred_at": now - timedelta(hours=3),
                    "affected_people": 2300,
                    "casualties": 0,
                    "economic_loss": 850.5,
                },
                {
                    "title": "丽江市宁蒗县发生山体滑坡",
                    "description": "受持续降雨影响，宁蒗彝族自治县发生山体滑坡，造成2间房屋损毁。",
                    "location": "云南省丽江市宁蒗彝族自治县",
                    "latitude": 27.29,
                    "longitude": 100.85,
                    "disaster_type": DisasterType.LANDSLIDE,
                    "severity": SeverityLevel.MEDIUM,
                    "occurred_at": now - timedelta(hours=6),
                    "affected_people": 45,
                    "casualties": 2,
                },
                {
                    "title": "西双版纳州发布高温橙色预警",
                    "description": "西双版纳州多地气温突破38℃，局地可达40℃以上，请注意防暑降温。",
                    "location": "云南省西双版纳傣族自治州",
                    "latitude": 22.00,
                    "longitude": 100.80,
                    "disaster_type": DisasterType.DROUGHT,
                    "severity": SeverityLevel.MEDIUM,
                    "occurred_at": now - timedelta(hours=1),
                    "affected_people": 0,
                    "casualties": 0,
                },
                {
                    "title": "大理州祥云县森林火情已得到控制",
                    "description": "祥云县发生森林火情，经过300余名扑火队员奋力扑救，火情已得到有效控制。",
                    "location": "云南省大理白族自治州祥云县",
                    "latitude": 25.47,
                    "longitude": 100.56,
                    "disaster_type": DisasterType.FOREST_FIRE,
                    "severity": SeverityLevel.HIGH,
                    "occurred_at": now - timedelta(hours=12),
                    "affected_people": 120,
                    "casualties": 0,
                    "economic_loss": 320.0,
                },
                {
                    "title": "曲靖市师宗县遭受冰雹灾害",
                    "description": "师宗县部分乡镇遭受冰雹袭击，最大冰雹直径约2厘米，农作物受灾严重。",
                    "location": "云南省曲靖市师宗县",
                    "latitude": 24.83,
                    "longitude": 103.98,
                    "disaster_type": DisasterType.STORM,
                    "severity": SeverityLevel.MEDIUM,
                    "occurred_at": now - timedelta(hours=5),
                    "affected_people": 1500,
                    "casualties": 0,
                    "economic_loss": 450.0,
                },
            ]

            for idx, evt_data in enumerate(mock_events):
                event_id = self._generate_event_id(self.source, f"{evt_data['title']}_{idx}")
                event = DisasterEvent(
                    id=event_id,
                    source=self.source,
                    source_url=None,
                    **evt_data,
                )
                events.append(event)

            logger.info(f"[{self.name}] 生成 {len(events)} 条模拟数据")
            return CrawlResult(
                source=self.source,
                total_count=len(events),
                new_count=len(events),
                events=events,
                error=None,
            )
        except Exception as e:
            logger.error(f"[{self.name}] 爬取失败: {e}")
            return CrawlResult(
                source=self.source,
                total_count=0,
                new_count=0,
                events=[],
                error=str(e),
            )


# 爬虫注册表
CRAWLER_REGISTRY: Dict[str, BaseCrawler] = {
    "mock": MockCrawler(),
}


def get_crawler(name: str) -> Optional[BaseCrawler]:
    """获取爬虫实例"""
    return CRAWLER_REGISTRY.get(name)


def get_all_crawlers() -> List[BaseCrawler]:
    """获取所有爬虫实例"""
    return list(CRAWLER_REGISTRY.values())
