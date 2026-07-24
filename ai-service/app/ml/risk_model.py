"""风险研判模型入口（从 pipeline 导入，保持向后兼容）"""
from app.pipeline.risk_model import risk_model, RiskAssessmentModel

__all__ = ["risk_model", "RiskAssessmentModel"]
