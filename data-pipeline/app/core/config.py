from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "云南省自然灾害应急决策数据管道服务"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    CRAWLER_INTERVAL_MINUTES: int = 30
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ENABLE_MOCK_CRAWLER: bool = False
    ENABLE_YUNNAN_NET_CRAWLER: bool = True

    SSE_KEEPALIVE_INTERVAL: int = 15
    SSE_RETRY_TIMEOUT: int = 3000

    YUNNAN_NET_KEYWORDS: List[str] = [
        "云南 地震",
        "云南 洪水",
        "云南 暴雨",
        "云南 山体滑坡",
        "云南 泥石流",
        "云南 森林火灾",
        "云南 干旱",
        "云南 冰雹",
        "云南 灾害",
        "昆明 地震",
        "昭通 洪涝",
        "曲靖 灾害",
        "丽江 滑坡",
        "普洱 地震",
        "大理 地震",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
