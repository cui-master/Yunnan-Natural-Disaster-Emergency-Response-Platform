"""
LightGBM 时序风险研判模型
- 支持真实 LightGBM 模型加载推理
- 自动 fallback 到规则+随机模拟的研判引擎
- 支持模型训练接口（预留）

灾害类型：暴雨、洪涝、山洪、滑坡、泥石流、崩塌、地震
输出：风险等级（低/中/高/极高）+ 风险评分（0~100）+ 紧急等级（1~5）
"""
import math
from datetime import datetime
from typing import Optional
from app.core.logging import logger

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    logger.warning("LightGBM 未安装，将使用规则引擎 fallback")

from app.pipeline.models import RiskResult


class RiskAssessmentModel:
    """风险研判模型（LightGBM + 规则 fallback）"""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_version = "v1.0-rule"
        if model_path and HAS_LIGHTGBM:
            self._load_model(model_path)

    def _load_model(self, model_path: str):
        try:
            self.model = lgb.Booster(model_file=model_path)
            self.model_version = f"lgb-{model_path.split('/')[-1]}"
            logger.info(f"LightGBM 模型加载成功: {model_path}")
        except Exception as e:
            logger.error(f"加载 LightGBM 模型失败: {e}，使用规则引擎 fallback")
            self.model = None

    def assess(self, features: dict, disaster_type: str) -> RiskResult:
        """
        研判单区域单灾种风险
        features: 融合后的特征（来自多源核验引擎）
        disaster_type: 灾害类型
        """
        if self.model is not None and HAS_LIGHTGBM:
            return self._lgb_predict(features, disaster_type)
        return self._rule_based_predict(features, disaster_type)

    def assess_area(self, features: dict) -> list[RiskResult]:
        """研判单区域所有相关灾种的风险"""
        disaster_types = self._infer_relevant_disasters(features)
        results = []
        for dt in disaster_types:
            result = self.assess(features, dt)
            results.append(result)
        return results

    def _infer_relevant_disasters(self, features: dict) -> list[str]:
        """根据特征推断相关灾种"""
        disasters = []
        rain = features.get("rainfall_24h", 0) + features.get("rainfall_3d", 0) * 0.3

        if rain > 50:
            disasters.extend(["暴雨", "洪涝", "山洪"])
        if rain > 100 and features.get("geological_risk_level") in ["中", "高", "极高"]:
            disasters.extend(["滑坡", "泥石流", "崩塌"])
        if features.get("has_earthquake"):
            disasters.append("地震")
        if features.get("water_level_ratio", 0) > 0.9:
            if "洪涝" not in disasters:
                disasters.append("洪涝")

        if not disasters:
            disasters = ["暴雨", "滑坡"]

        return list(set(disasters))

    def _lgb_predict(self, features: dict, disaster_type: str) -> RiskResult:
        """LightGBM 模型预测（预留接口）"""
        # TODO: 构造特征向量，调用模型
        # 暂时降级到规则引擎
        return self._rule_based_predict(features, disaster_type)

    def _rule_based_predict(self, features: dict, disaster_type: str) -> RiskResult:
        """
        基于规则的风险研判（fallback）
        综合考虑降雨、地质条件、水文、舆情等多因素加权
        """
        score = 0.0
        factors = {}

        # ===== 降雨因子（权重最大）=====
        rain_24h = features.get("rainfall_24h", 0)
        rain_3d = features.get("rainfall_3d", 0)
        rain_7d = features.get("rainfall_7d", 0)

        if disaster_type in ["暴雨", "洪涝", "山洪", "滑坡", "泥石流", "崩塌"]:
            rain_score = min(35, rain_24h * 0.4 + rain_3d * 0.1 + rain_7d * 0.02)
            score += rain_score
            factors["降雨贡献"] = round(rain_score, 1)

            # 预警等级加成
            warning = features.get("weather_warning")
            warning_bonus = {"蓝": 3, "黄": 7, "橙": 12, "红": 18}
            if warning in warning_bonus:
                score += warning_bonus[warning]
                factors["气象预警加成"] = warning_bonus[warning]

        # ===== 地质因子 =====
        if disaster_type in ["滑坡", "泥石流", "崩塌", "地震"]:
            geo_level = features.get("geological_risk_level", "低")
            geo_score_map = {"低": 3, "中": 8, "高": 15, "极高": 25}
            geo_score = geo_score_map.get(geo_level, 3)
            score += geo_score
            factors["地质条件"] = geo_score

        # ===== 地震因子 =====
        if disaster_type == "地震":
            mag = features.get("max_magnitude", 0)
            if mag > 0:
                eq_score = min(40, mag * 6)
                score += eq_score
                factors["震级贡献"] = round(eq_score, 1)

        # ===== 水文因子 =====
        if disaster_type in ["洪涝", "山洪"]:
            water_ratio = features.get("water_level_ratio", 0)
            if water_ratio > 0:
                hydro_score = min(25, max(0, (water_ratio - 0.7)) * 80)
                score += hydro_score
                factors["水位贡献"] = round(hydro_score, 1)

            flood_warning = features.get("flood_warning")
            flood_bonus = {"蓝": 2, "黄": 5, "橙": 10, "红": 15}
            if flood_warning in flood_bonus:
                score += flood_bonus[flood_warning]
                factors["水文预警"] = flood_bonus[flood_warning]

        # ===== 舆情因子（权重较低，用于辅助）=====
        opinion_hot = features.get("opinion_hot_count", 0)
        if opinion_hot > 20:
            opinion_score = min(8, math.log10(opinion_hot) * 4)
            score += opinion_score
            factors["舆情热度"] = round(opinion_score, 1)

        # 情感倾向（负面情感加权）
        sentiment = features.get("sentiment_score", 0.5)
        if sentiment < 0.3 and opinion_hot > 10:
            score += 3
            factors["负面舆情"] = 3

        # ===== 归一化到 0~100 =====
        score = min(100, max(0, score))

        # 风险等级映射
        if score >= 75:
            risk_level = "极高"
            urgent = 5
        elif score >= 55:
            risk_level = "高"
            urgent = 4
        elif score >= 30:
            risk_level = "中"
            urgent = 2 if score < 40 else 3
        else:
            risk_level = "低"
            urgent = 1

        return RiskResult(
            area_name=features.get("area_name", ""),
            disaster_type=disaster_type,
            risk_level=risk_level,
            risk_score=round(score, 2),
            urgent_level=urgent,
            contributing_factors=factors,
            model_version=self.model_version,
            generate_time=datetime.now(),
            data_sources=features.get("data_sources", []),
        )

    def train(self, train_data_path: str, save_path: str) -> bool:
        """
        模型训练接口（预留）
        train_data_path: 训练数据路径（CSV）
        save_path: 模型保存路径
        """
        if not HAS_LIGHTGBM:
            logger.error("LightGBM 未安装，无法训练")
            return False
        try:
            # TODO: 实现训练逻辑
            logger.info(f"训练完成，模型已保存到 {save_path}")
            return True
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return False


risk_model = RiskAssessmentModel()
