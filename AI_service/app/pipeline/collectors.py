"""
数据采集器基类 + 四大类采集器实现
- WeatherCollector: 气象数据（降雨、气温、预警）
- GeologyCollector: 地质数据（地震速报、地质灾害气象风险）
- HydrologyCollector: 水文数据（水位、流量、水库）
- PublicOpinionCollector: 舆情数据（社交平台、新闻爬虫）

每个采集器支持两种模式：
  1. 模拟模式（默认）：生成符合云南地理特征的仿真数据
  2. 真实模式：预留接口，后续接入真实 API
"""
import random
import math
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from app.core.logging import logger
from app.pipeline.models import (
    WeatherData, GeologyData, HydrologyData, PublicOpinionData,
)


class BaseCollector(ABC):
    """采集器基类"""
    name: str = "base"

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode

    @abstractmethod
    async def collect(self, area_name: str) -> list:
        """采集指定区域的数据，返回数据列表"""
        pass

    async def collect_batch(self, area_list: list[str]) -> list:
        """批量采集多个区域"""
        results = []
        for area in area_list:
            try:
                data = await self.collect(area)
                results.extend(data)
            except Exception as e:
                logger.error(f"[{self.name}] 采集 {area} 失败: {e}")
        logger.info(f"[{self.name}] 采集完成，共 {len(results)} 条数据")
        return results


class WeatherCollector(BaseCollector):
    """气象数据采集器"""
    name = "weather"

    # 云南各区域降雨基线（雨季/旱季模拟）
    RAIN_BASELINE = {
        "昭通市镇雄县": {"rainy": 45.0, "dry": 8.0},
        "昆明市东川区": {"rainy": 35.0, "dry": 5.0},
        "大理州漾濞县": {"rainy": 40.0, "dry": 12.0},
        "怒江州贡山县": {"rainy": 80.0, "dry": 20.0},
        "普洱市澜沧县": {"rainy": 55.0, "dry": 15.0},
        "楚雄州南华县": {"rainy": 30.0, "dry": 6.0},
        "丽江市宁蒗县": {"rainy": 25.0, "dry": 4.0},
        "红河州元阳县": {"rainy": 50.0, "dry": 8.0},
        "文山州广南县": {"rainy": 55.0, "dry": 10.0},
        "德宏州盈江县": {"rainy": 65.0, "dry": 18.0},
    }

    async def collect(self, area_name: str) -> list[WeatherData]:
        if self.mock_mode:
            return [self._mock_weather(area_name)]
        return []

    def _mock_weather(self, area_name: str) -> WeatherData:
        baseline = self.RAIN_BASELINE.get(area_name, {"rainy": 40.0, "dry": 10.0})
        now = datetime.now()
        # 6-9月雨季，其余旱季
        is_rainy = 6 <= now.month <= 9
        base = baseline["rainy"] if is_rainy else baseline["dry"]

        # 随机生成带波动的降雨量
        factor = random.uniform(0.1, 2.5)
        rain_24h = round(base * factor * random.uniform(0.7, 1.3), 1)
        rain_3d = round(rain_24h * random.uniform(2.0, 3.5), 1)
        rain_7d = round(rain_3d * random.uniform(1.8, 2.8), 1)

        # 降雨强度分级
        if rain_24h >= 100:
            intensity = "大暴雨"
            warning = "红"
        elif rain_24h >= 50:
            intensity = "暴雨"
            warning = "橙"
        elif rain_24h >= 25:
            intensity = "大雨"
            warning = "黄"
        elif rain_24h >= 10:
            intensity = "中雨"
            warning = "蓝"
        else:
            intensity = "小雨"
            warning = None

        return WeatherData(
            area_name=area_name,
            temperature=round(random.uniform(15, 32), 1),
            rainfall_24h=rain_24h,
            rainfall_3d=rain_3d,
            rainfall_7d=rain_7d,
            rainfall_intensity=intensity,
            wind_speed=round(random.uniform(2, 20), 1),
            humidity=round(random.uniform(50, 95), 1),
            warning_level=warning,
            forecast_hours=24,
            reliability=0.85 + random.uniform(-0.05, 0.05),
            collect_time=now,
        )


class GeologyCollector(BaseCollector):
    """地质数据采集器"""
    name = "geology"

    # 地震活跃区域概率
    EARTHQUAKE_HOTSPOTS = {
        "大理州漾濞县": 0.15,
        "普洱市澜沧县": 0.12,
        "丽江市宁蒗县": 0.10,
        "德宏州盈江县": 0.08,
        "昭通市镇雄县": 0.05,
        "怒江州贡山县": 0.06,
    }

    async def collect(self, area_name: str) -> list[GeologyData]:
        if self.mock_mode:
            return [self._mock_geology(area_name)]
        return []

    def _mock_geology(self, area_name: str) -> GeologyData:
        # 地质灾害气象风险（与降雨关联，这里简化模拟）
        risk_levels = ["低", "中", "高", "极高"]
        base_idx = 0
        if "东川" in area_name or "贡山" in area_name or "元阳" in area_name:
            base_idx = 1

        # 随机触发地震事件（低概率）
        eq_prob = self.EARTHQUAKE_HOTSPOTS.get(area_name, 0.02)
        has_earthquake = random.random() < eq_prob

        magnitude = None
        depth = None
        event_type = None
        occ_time = None

        if has_earthquake:
            magnitude = round(random.uniform(2.0, 5.5), 1)
            depth = round(random.uniform(5, 30), 1)
            event_type = "地震"
            occ_time = datetime.now() - timedelta(hours=random.randint(0, 12))

        # 地质灾害风险等级（结合地形）
        risk_idx = min(3, base_idx + random.randint(0, 2))
        slope_stability = round(random.uniform(0.6, 1.5), 2)

        return GeologyData(
            area_name=area_name,
            event_type=event_type,
            magnitude=magnitude,
            depth=depth,
            occurrence_time=occ_time,
            geological_risk_level=risk_levels[risk_idx],
            slope_stability=slope_stability,
            reliability=0.90 + random.uniform(-0.05, 0.05),
            collect_time=datetime.now(),
        )


class HydrologyCollector(BaseCollector):
    """水文数据采集器"""
    name = "hydrology"

    # 主要江河与对应区域
    RIVER_MAP = {
        "昭通市镇雄县": "赤水河",
        "昆明市东川区": "小江",
        "大理州漾濞县": "漾濞江",
        "怒江州贡山县": "怒江",
        "普洱市澜沧县": "澜沧江",
        "楚雄州南华县": "龙川江",
        "丽江市宁蒗县": "金沙江",
        "红河州元阳县": "红河",
        "文山州广南县": "西洋江",
        "德宏州盈江县": "大盈江",
    }

    async def collect(self, area_name: str) -> list[HydrologyData]:
        if self.mock_mode:
            return [self._mock_hydrology(area_name)]
        return []

    def _mock_hydrology(self, area_name: str) -> HydrologyData:
        river = self.RIVER_MAP.get(area_name, "金沙江")
        base_level = random.uniform(800, 1500)  # 基础水位（海拔相关，简化）

        # 水位波动
        water_level = round(base_level + random.uniform(-2, 8), 2)
        warning_level = round(base_level + 5, 2)

        # 是否超警戒
        flood_warning = None
        if water_level >= warning_level * 1.05:
            flood_warning = "橙"
        elif water_level >= warning_level:
            flood_warning = "黄"
        elif water_level >= warning_level * 0.95:
            flood_warning = "蓝"

        return HydrologyData(
            area_name=area_name,
            river_name=river,
            water_level=water_level,
            warning_water_level=warning_level,
            flow_rate=round(random.uniform(50, 2000), 1),
            reservoir_level=round(base_level + random.uniform(0, 10), 2),
            reservoir_storage=round(random.uniform(1000, 50000), 0),
            flood_warning=flood_warning,
            reliability=0.80 + random.uniform(-0.05, 0.05),
            collect_time=datetime.now(),
        )


class PublicOpinionCollector(BaseCollector):
    """舆情数据采集器（模拟）"""
    name = "public_opinion"

    HOT_TOPICS_POOL = [
        "山体滑坡", "道路中断", "村民被困", "泥石流",
        "房屋倒塌", "桥梁冲毁", "暴雨红色预警", "水库泄洪",
        "人员失联", "应急响应", "救援队伍", "物资调配",
        "地震速报", "余震", "崩塌", "山洪暴发",
    ]

    async def collect(self, area_name: str) -> list[PublicOpinionData]:
        if self.mock_mode:
            return [self._mock_opinion(area_name)]
        return []

    def _mock_opinion(self, area_name: str) -> PublicOpinionData:
        # 随机决定舆情热度
        hot = random.random() < 0.3

        if hot:
            hot_count = random.randint(10, 200)
            neg_count = random.randint(5, hot_count)
            sentiment = round(random.uniform(0.1, 0.4), 2)
            topics = random.sample(self.HOT_TOPICS_POOL, random.randint(2, 5))
            speed = random.choice(["缓慢", "中等", "快速", "爆发式"])
            first_time = datetime.now() - timedelta(hours=random.randint(1, 48))
        else:
            hot_count = random.randint(0, 5)
            neg_count = random.randint(0, hot_count)
            sentiment = round(random.uniform(0.5, 0.9), 2)
            topics = random.sample(self.HOT_TOPICS_POOL, random.randint(0, 1))
            speed = None
            first_time = None

        return PublicOpinionData(
            area_name=area_name,
            keyword=area_name,
            hot_post_count=hot_count,
            negative_count=neg_count,
            sentiment_score=sentiment,
            hot_topics=topics,
            first_report_time=first_time,
            spreading_speed=speed,
            reliability=0.55 + random.uniform(-0.1, 0.1),
            collect_time=datetime.now(),
        )


class CollectorManager:
    """采集器管理器"""

    def __init__(self, mock_mode: bool = True):
        self.collectors = {
            "weather": WeatherCollector(mock_mode=mock_mode),
            "geology": GeologyCollector(mock_mode=mock_mode),
            "hydrology": HydrologyCollector(mock_mode=mock_mode),
            "public_opinion": PublicOpinionCollector(mock_mode=mock_mode),
        }

    async def collect_all(self, area_list: list[str]) -> dict:
        """调用所有采集器，返回按类型分组的数据"""
        results = {}
        for name, collector in self.collectors.items():
            try:
                data = await collector.collect_batch(area_list)
                results[name] = data
            except Exception as e:
                logger.error(f"采集器 {name} 执行失败: {e}")
                results[name] = []
        return results

    async def collect_by_type(self, source_type: str, area_list: list[str]) -> list:
        """按类型调用采集器"""
        collector = self.collectors.get(source_type)
        if not collector:
            raise ValueError(f"未知采集器类型: {source_type}")
        return await collector.collect_batch(area_list)


collector_manager = CollectorManager()
