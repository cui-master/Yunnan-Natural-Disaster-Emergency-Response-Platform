from app.crawlers.base import BaseCrawler, MockCrawler
from app.crawlers.base import CRAWLER_REGISTRY as _base_registry
from app.core.config import settings
from app.core.logging import logger

CRAWLER_REGISTRY = _base_registry

if not settings.ENABLE_MOCK_CRAWLER:
    if "mock" in CRAWLER_REGISTRY:
        del CRAWLER_REGISTRY["mock"]
        logger.info("Mock 爬虫已禁用")

if settings.ENABLE_YUNNAN_NET_CRAWLER:
    from app.crawlers.yunnan_net import YunnanNetCrawler

    crawler = YunnanNetCrawler(keywords=settings.YUNNAN_NET_KEYWORDS)
    CRAWLER_REGISTRY["yunnan_net"] = crawler
    logger.info(f"云南网爬虫已启用，关键词数量: {len(settings.YUNNAN_NET_KEYWORDS)}")


def get_crawler(name: str):
    return CRAWLER_REGISTRY.get(name)


def get_all_crawlers():
    return list(CRAWLER_REGISTRY.values())


__all__ = [
    "BaseCrawler",
    "MockCrawler",
    "YunnanNetCrawler" if settings.ENABLE_YUNNAN_NET_CRAWLER else "MockCrawler",
    "CRAWLER_REGISTRY",
    "get_crawler",
    "get_all_crawlers",
]
