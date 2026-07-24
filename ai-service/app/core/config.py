from pydantic_settings import BaseSettings
from typing import Optional, Dict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "云南省自然灾害应急决策AI服务"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8050
    DEBUG: bool = False

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "12345678"
    NEO4J_DATABASE: str = "neo4j"

    # Dify 调度方案工作流
    DIFY_BASE_URL: str = "http://localhost:5001"
    DIFY_API_KEY: str = ""
    DIFY_WORKFLOW_ID: str = "natural-disaster-workflow"

    # Dify 风险评估工作流（与调度方案区分）
    DIFY_RISK_API_KEY: str = ""

    # Dify 知识库
    DIFY_DATASET_API_KEY: str = ""
    DIFY_DATASET_BASE_URL: str = "http://localhost:5001"

    # 知识库名称与 ID 映射
    KB_OPTIMIZE_DISPATCH_ID: str = "a154e469-3acd-4c33-bcdc-ea65d0886488"
    KB_RISK_ASSESSMENT_ID: str = "03d787b9-e585-4b85-abbe-332e208c6530"

    # ============== LLM 降级配置 ==============
    # 当前 LLM provider（deepseek / qwen），运行时可被 admin 接口动态修改
    LLM_PROVIDER: str = "deepseek"

    # DeepSeek V4 推理模型
    DEEPSEEK_API_KEY: str = "sk-acbf853086084ea3a8f1bcd807e073ae"
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"

    # 通义千问
    QWEN_API_KEY: str = ""
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-plus"

    # Business
    RISK_LEVEL_SYNC_INTERVAL_MINUTES: int = 30

    @property
    def KB_MAP(self) -> Dict[str, str]:
        return {
            "优化调度": self.KB_OPTIMIZE_DISPATCH_ID,
            "风险评估": self.KB_RISK_ASSESSMENT_ID,
        }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
