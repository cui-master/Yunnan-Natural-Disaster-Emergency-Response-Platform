# 爬虫扩展开发指南

本指南介绍如何为数据管道服务开发新的爬虫数据源。

## 目录结构

```
data-pipeline/
└── app/
    └── crawlers/
        ├── __init__.py
        ├── base.py          # 基类和注册表
        └── your_crawler.py  # 你的爬虫
```

## 创建新爬虫

### 第一步：创建爬虫文件

在 `app/crawlers/` 目录下创建新的爬虫文件，例如 `weather_crawler.py`：

```python
from app.crawlers.base import BaseCrawler
from app.models.schemas import (
    DisasterEvent,
    DisasterType,
    SeverityLevel,
    CrawlResult,
)
from app.core.logging import logger
import httpx
from bs4 import BeautifulSoup
from datetime import datetime


class YunnanWeatherCrawler(BaseCrawler):
    """云南省气象数据爬虫"""

    name = "yn_weather"
    source = "云南省气象局"

    async def crawl(self) -> CrawlResult:
        try:
            events = []
            
            # 1. 请求数据
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://example.com/weather/api",
                    headers={"User-Agent": self._user_agent()},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

            # 2. 解析数据
            for item in data.get("alerts", []):
                event = self._parse_alert(item)
                if event:
                    events.append(event)

            # 3. 返回结果
            logger.info(f"[{self.name}] 爬取完成，共 {len(events)} 条")
            return CrawlResult(
                source=self.source,
                total_count=len(events),
                new_count=0,  # 由 EventStore 计算
                events=events,
            )

        except Exception as e:
            logger.error(f"[{self.name}] 爬取失败: {e}")
            return CrawlResult(
                source=self.source,
                total_count=0,
                events=[],
                error=str(e),
            )

    def _parse_alert(self, item: dict) -> DisasterEvent | None:
        """解析单条预警信息"""
        try:
            event_id = self._generate_event_id(self.source, item["id"])
            disaster_type = self._parse_disaster_type(item["title"])
            severity = self._parse_severity(item["level"])

            return DisasterEvent(
                id=event_id,
                disaster_type=disaster_type,
                title=item["title"],
                description=item.get("content"),
                location=item["area"],
                severity=severity,
                occurred_at=datetime.fromisoformat(item["publish_time"]),
                source=self.source,
                source_url=item.get("url"),
                raw_data=item,
            )
        except Exception as e:
            logger.warning(f"[{self.name}] 解析失败: {e}")
            return None

    def _user_agent(self) -> str:
        from app.core.config import settings
        return settings.CRAWLER_USER_AGENT
```

### 第二步：注册爬虫

编辑 `app/crawlers/__init__.py`，将新爬虫添加到注册表：

```python
from app.crawlers.base import (
    BaseCrawler,
    MockCrawler,
    CRAWLER_REGISTRY,
    get_crawler,
    get_all_crawlers,
)
from app.crawlers.weather_crawler import YunnanWeatherCrawler  # 导入

# 注册新爬虫
CRAWLER_REGISTRY["yn_weather"] = YunnanWeatherCrawler()

__all__ = [
    "BaseCrawler",
    "MockCrawler",
    "YunnanWeatherCrawler",
    "CRAWLER_REGISTRY",
    "get_crawler",
    "get_all_crawlers",
]
```

或者直接修改 `base.py` 中的 `CRAWLER_REGISTRY` 字典。

### 第三步：配置（可选）

在 `.env` 文件中添加配置项：

```env
# 数据源开关
DATA_SOURCE_YN_WEATHER=true

# 自定义配置
YN_WEATHER_API_URL=https://example.com/api
YN_WEATHER_API_KEY=your_api_key
```

在 `app/core/config.py` 中添加：

```python
class Settings(BaseSettings):
    # ... 其他配置
    DATA_SOURCE_YN_WEATHER: bool = True
    YN_WEATHER_API_URL: str = ""
    YN_WEATHER_API_KEY: str = ""
```

## 基类提供的工具方法

`BaseCrawler` 提供以下辅助方法：

| 方法 | 说明 |
|------|------|
| `_generate_event_id(source, unique_key)` | 生成事件唯一ID |
| `_parse_severity(level)` | 解析严重程度（支持中文等级关键词） |
| `_parse_disaster_type(text)` | 根据文本推断灾害类型 |

## 最佳实践

1. **异常处理**: 爬虫内部必须捕获所有异常，通过 `CrawlResult.error` 返回
2. **超时设置**: HTTP 请求必须设置合理的超时时间
3. **请求频率**: 遵守目标网站的 robots.txt，设置合理的请求间隔
4. **数据验证**: 解析后的数据应验证完整性，缺失重要字段的记录应丢弃
5. **日志记录**: 使用 `logger.info/error/warning` 记录关键节点
6. **原始数据**: 在 `raw_data` 字段中保留原始数据，便于后续排查

## 测试爬虫

```bash
# 触发指定爬虫
curl -X POST http://127.0.0.1:8000/api/v1/crawler/run/yn_weather

# 查看爬取历史
curl http://127.0.0.1:8000/api/v1/crawler/history

# 查看事件列表
curl http://127.0.0.1:8000/api/v1/events
```
