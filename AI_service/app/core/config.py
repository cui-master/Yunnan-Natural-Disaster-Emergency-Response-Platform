from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "云南省自然灾害应急决策AI服务"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "12345678"
    NEO4J_DATABASE: str = "neo4j"

<<<<<<< HEAD
    # Dify 工作流（方案生成）—— 使用应用密钥 app-xxx
    DIFY_BASE_URL: str = "http://localhost:8083"
    DIFY_API_KEY: str = ""
    DIFY_WORKFLOW_ID: str = "natural-disaster-workflow"

    # Dify 知识库（Dataset）—— 注意使用 **Dataset API Key**（dataset-xxx），非应用密钥
    DIFY_DATASET_BASE_URL: str = "http://localhost:8083"
    DIFY_DATASET_API_KEY: str = ""
    KB_OPTIMIZE_DISPATCH_ID: str = "a154e469-3acd-4c33-bcdc-ea65d0886488"
    KB_RISK_ASSESSMENT_ID: str = "03d787b9-e585-4b85-abbe-332e208c6530"

=======
    # Dify
    DIFY_BASE_URL: str = "http://localhost:5001"
    DIFY_API_KEY: str = ""
    DIFY_WORKFLOW_ID: str = "natural-disaster-workflow"

>>>>>>> feature-cui
    # Business
    RISK_LEVEL_SYNC_INTERVAL_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
