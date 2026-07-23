"""
数据校验与多源核验引擎
1. 格式校验：检查必填字段、数值范围、数据类型
2. 多源核验：同一指标来自不同数据源时，按可信度加权融合
3. 异常值检测：识别明显不合理的数据
"""
from typing import Any
from app.core.logging import logger
from app.pipeline.models import (
    WeatherData, GeologyData, HydrologyData, PublicOpinionData,
)


class DataValidator:
    """数据格式校验器"""

    # 各字段合法范围
    RANGES = {
        "temperature": (-40, 50),
        "rainfall_24h": (0, 1000),
        "rainfall_3d": (0, 3000),
        "rainfall_7d": (0, 5000),
        "humidity": (0, 100),
        "wind_speed": (0, 80),
        "magnitude": (0, 10),
        "depth": (0, 700),
        "water_level": (0, 10000),
        "flow_rate": (0, 100000),
        "hot_post_count": (0, 100000),
        "sentiment_score": (0, 1),
        "reliability": (0, 1),
        "slope_stability": (0.1, 5),
    }

    RISK_LEVELS = {"低", "中", "高", "极高"}
    WARNING_LEVELS = {"蓝", "黄", "橙", "红"}

    @classmethod
    def validate_weather(cls, data: WeatherData) -> tuple[bool, list[str]]:
        errors = []
        if not data.area_name:
            errors.append("area_name 必填")
        if data.rainfall_24h < 0:
            errors.append("降雨量不能为负")
        if data.temperature is not None and not (cls.RANGES["temperature"][0] <= data.temperature <= cls.RANGES["temperature"][1]):
            errors.append(f"温度 {data.temperature} 超出合理范围")
        if data.humidity is not None and not (0 <= data.humidity <= 100):
            errors.append("湿度超出 0~100 范围")
        if data.warning_level and data.warning_level not in cls.WARNING_LEVELS:
            errors.append(f"预警等级 {data.warning_level} 不合法")
        return (len(errors) == 0, errors)

    @classmethod
    def validate_geology(cls, data: GeologyData) -> tuple[bool, list[str]]:
        errors = []
        if not data.area_name:
            errors.append("area_name 必填")
        if data.magnitude is not None and not (0 <= data.magnitude <= 10):
            errors.append(f"震级 {data.magnitude} 超出范围")
        if data.geological_risk_level and data.geological_risk_level not in cls.RISK_LEVELS:
            errors.append(f"地质风险等级 {data.geological_risk_level} 不合法")
        return (len(errors) == 0, errors)

    @classmethod
    def validate_hydrology(cls, data: HydrologyData) -> tuple[bool, list[str]]:
        errors = []
        if not data.area_name:
            errors.append("area_name 必填")
        if data.water_level is not None and data.water_level < 0:
            errors.append("水位不能为负")
        if data.flow_rate is not None and data.flow_rate < 0:
            errors.append("流量不能为负")
        return (len(errors) == 0, errors)

    @classmethod
    def validate_public_opinion(cls, data: PublicOpinionData) -> tuple[bool, list[str]]:
        errors = []
        if not data.area_name:
            errors.append("area_name 必填")
        if data.hot_post_count < 0:
            errors.append("舆情数量不能为负")
        if not (0 <= data.sentiment_score <= 1):
            errors.append("情感分超出 0~1 范围")
        if not (0 <= data.reliability <= 1):
            errors.append("可信度超出 0~1 范围")
        return (len(errors) == 0, errors)

    @classmethod
    def validate_all(cls, weather_list: list[WeatherData],
                     geology_list: list[GeologyData],
                     hydrology_list: list[HydrologyData],
                     opinion_list: list[PublicOpinionData]) -> dict:
        """批量校验所有数据，返回校验结果统计"""
        stats = {"total": 0, "valid": 0, "invalid": 0, "errors_by_type": {}}

        def _validate_batch(data_list, validator, name):
            valid_list = []
            error_count = 0
            for d in data_list:
                ok, errs = validator(d)
                if ok:
                    valid_list.append(d)
                else:
                    error_count += 1
                    logger.warning(f"[{name}] 数据校验失败 {d.area_name}: {errs}")
            stats["errors_by_type"][name] = error_count
            stats["total"] += len(data_list)
            stats["valid"] += len(valid_list)
            stats["invalid"] += error_count
            return valid_list

        result = {
            "weather": _validate_batch(weather_list, cls.validate_weather, "weather"),
            "geology": _validate_batch(geology_list, cls.validate_geology, "geology"),
            "hydrology": _validate_batch(hydrology_list, cls.validate_hydrology, "hydrology"),
            "public_opinion": _validate_batch(opinion_list, cls.validate_public_opinion, "public_opinion"),
        }
        result["_stats"] = stats
        logger.info(f"数据校验完成：共 {stats['total']} 条，有效 {stats['valid']}，无效 {stats['invalid']}")
        return result


class MultiSourceFusionEngine:
    """
    多源数据融合引擎
    对同一区域的同类指标，按可信度加权融合，得到最终研判值
    """

    # 各类数据源基础权重
    SOURCE_BASE_WEIGHT = {
        "geology_magnitude": 1.0,
        "weather_rainfall": 0.8,
        "hydrology_water_level": 0.7,
        "geology_risk": 0.85,
        "weather_warning": 0.75,
        "hydrology_flood_warning": 0.65,
        "opinion_heat": 0.4,
    }

    @classmethod
    def fuse_area_data(cls, area_name: str,
                       weather_list: list[WeatherData],
                       geology_list: list[GeologyData],
                       hydrology_list: list[HydrologyData],
                       opinion_list: list[PublicOpinionData]) -> dict:
        """
        融合单区域所有数据源，得到结构化特征字典
        返回可直接输入模型的特征向量
        """
        area_weather = [w for w in weather_list if w.area_name == area_name]
        area_geology = [g for g in geology_list if g.area_name == area_name]
        area_hydro = [h for h in hydrology_list if h.area_name == area_name]
        area_opinion = [o for o in opinion_list if o.area_name == area_name]

        # 加权融合降雨
        rain_24h = cls._weighted_avg([w.rainfall_24h for w in area_weather],
                                      [w.reliability for w in area_weather])
        rain_3d = cls._weighted_avg([w.rainfall_3d for w in area_weather],
                                    [w.reliability for w in area_weather])
        rain_7d = cls._weighted_avg([w.rainfall_7d for w in area_weather],
                                    [w.reliability for w in area_weather])

        # 最高预警等级
        weather_warning = cls._max_warning_level([w.warning_level for w in area_weather if w.warning_level])
        flood_warning = cls._max_warning_level([h.flood_warning for h in area_hydro if h.flood_warning])

        # 地质相关
        geo_risk = None
        for g in area_geology:
            if g.geological_risk_level:
                geo_risk = g.geological_risk_level
                break

        max_magnitude = max([g.magnitude for g in area_geology if g.magnitude is not None], default=None)
        has_earthquake = max_magnitude is not None and max_magnitude >= 3.0

        # 水位比（当前水位/警戒水位）
        water_level_ratio = 0.0
        for h in area_hydro:
            if h.water_level and h.warning_water_level and h.warning_water_level > 0:
                ratio = h.water_level / h.warning_water_level
                water_level_ratio = max(water_level_ratio, ratio)

        # 舆情热度
        total_hot = sum(o.hot_post_count for o in area_opinion)
        avg_sentiment = cls._weighted_avg(
            [o.sentiment_score for o in area_opinion],
            [o.reliability for o in area_opinion],
        )

        # 综合特征
        features = {
            "area_name": area_name,
            "rainfall_24h": rain_24h or 0.0,
            "rainfall_3d": rain_3d or 0.0,
            "rainfall_7d": rain_7d or 0.0,
            "weather_warning": weather_warning,
            "geological_risk_level": geo_risk or "低",
            "has_earthquake": has_earthquake,
            "max_magnitude": max_magnitude or 0.0,
            "water_level_ratio": water_level_ratio,
            "flood_warning": flood_warning,
            "opinion_hot_count": total_hot,
            "sentiment_score": avg_sentiment or 0.5,
            "data_sources": [
                src for src, has_data in [
                    ("weather", len(area_weather) > 0),
                    ("geology", len(area_geology) > 0),
                    ("hydrology", len(area_hydro) > 0),
                    ("public_opinion", len(area_opinion) > 0),
                ] if has_data
            ],
        }
        return features

    @classmethod
    def _weighted_avg(cls, values: list[float], weights: list[float]) -> float | None:
        if not values or not weights:
            return None
        total_w = sum(weights)
        if total_w == 0:
            return None
        return sum(v * w for v, w in zip(values, weights)) / total_w

    @classmethod
    def _max_warning_level(cls, levels: list[str]) -> str | None:
        if not levels:
            return None
        order = {"蓝": 1, "黄": 2, "橙": 3, "红": 4}
        max_lvl = max(levels, key=lambda x: order.get(x, 0))
        return max_lvl


data_validator = DataValidator()
fusion_engine = MultiSourceFusionEngine()
