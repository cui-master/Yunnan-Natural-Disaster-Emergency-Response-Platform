# 数据管道服务 API 文档

## 概述

数据管道服务为云南省自然灾害应急决策平台提供实时灾害数据采集与推送能力。服务支持 SSE（Server-Sent Events）实时推送和 REST API 两种调用方式，可直接对接 Dify 工作流。

## 服务信息

- **服务地址**: `http://127.0.0.1:8000`
- **传输方式**: SSE (Server-Sent Events)
- **SSE 端点**: `/api/v1/sse` （兼容路径: `/sse`）
- **API 文档**: `/docs` (Swagger UI)

## Dify 配置

在 Dify 工作流中配置 MCP/SSE 数据源：

```json
{
  "crawler_service": {
    "transport": "sse",
    "url": "http://127.0.0.1:8000/sse"
  }
}
```

## SSE 事件类型

### 1. connected - 连接成功

客户端连接成功后立即发送。

```json
{
  "event": "connected",
  "data": {
    "status": "connected",
    "client_count": 1,
    "stats": {
      "total_events": 6,
      "last_crawl_time": "2024-01-15T10:30:00",
      "by_type": { "earthquake": 1, "flood": 1 },
      "by_severity": { "high": 2, "medium": 3 }
    }
  }
}
```

### 2. new_event - 新灾害事件

当爬取到新的灾害事件时推送。

```json
{
  "event": "new_event",
  "data": {
    "id": "abc123",
    "disaster_type": "earthquake",
    "title": "昆明市盘龙区发生3.2级地震",
    "description": "据云南省地震台网测定...",
    "location": "云南省昆明市盘龙区",
    "latitude": 25.05,
    "longitude": 102.72,
    "severity": "low",
    "occurred_at": "2024-01-15T10:15:00",
    "source": "模拟数据",
    "source_url": null,
    "affected_people": 0,
    "casualties": 0,
    "economic_loss": null
  }
}
```

### 3. crawl_result - 爬取结果

每次爬取任务完成后推送。

```json
{
  "event": "crawl_result",
  "data": {
    "source": "模拟数据",
    "total_count": 6,
    "new_count": 2,
    "error": null,
    "crawled_at": "2024-01-15T10:30:00"
  }
}
```

### 4. keepalive - 心跳保活

每 15 秒发送一次心跳，保持连接活跃。

```json
{
  "event": "keepalive",
  "data": {
    "status": "alive",
    "timestamp": 1234567890.123
  }
}
```

## REST API

### 灾害事件

#### 获取事件列表

```
GET /api/v1/events?disaster_type=earthquake&severity=high&location=昆明&hours=24&limit=50
```

**查询参数**:
- `disaster_type` (可选): 灾害类型 (earthquake/flood/typhoon/drought/landslide/forest_fire/storm/other)
- `severity` (可选): 严重程度 (low/medium/high/critical)
- `location` (可选): 地点关键词
- `hours` (可选): 最近N小时内
- `limit` (可选): 返回数量限制，默认100

#### 获取事件详情

```
GET /api/v1/events/{event_id}
```

#### 获取事件统计

```
GET /api/v1/events/stats/summary
```

### 爬虫管理

#### 获取爬虫列表

```
GET /api/v1/crawler/crawlers
```

#### 触发全量爬取

```
POST /api/v1/crawler/run
```

#### 触发指定爬虫

```
POST /api/v1/crawler/run/{crawler_name}
```

#### 获取爬取历史

```
GET /api/v1/crawler/history?limit=20
```

### 健康检查

```
GET /health
```

## 灾害类型枚举

| 类型值 | 说明 |
|--------|------|
| earthquake | 地震 |
| flood | 洪水/洪涝 |
| typhoon | 台风 |
| drought | 干旱 |
| landslide | 滑坡/泥石流 |
| forest_fire | 森林火灾 |
| storm | 风暴/冰雹 |
| other | 其他 |

## 严重程度枚举

| 程度值 | 说明 |
|--------|------|
| low | 低 |
| medium | 中 |
| high | 高 |
| critical | 极重 |

## 示例：JavaScript 客户端

```javascript
const eventSource = new EventSource('http://127.0.0.1:8000/api/v1/sse');

eventSource.addEventListener('connected', (e) => {
    const data = JSON.parse(e.data);
    console.log('连接成功:', data);
});

eventSource.addEventListener('new_event', (e) => {
    const event = JSON.parse(e.data);
    console.log('新灾害事件:', event);
});

eventSource.addEventListener('crawl_result', (e) => {
    const result = JSON.parse(e.data);
    console.log('爬取结果:', result);
});

eventSource.onerror = (err) => {
    console.error('SSE 错误:', err);
};
```

## 示例：Python 客户端

```python
import httpx
import json

async def listen_sse():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET",
            "http://127.0.0.1:8000/api/v1/sse",
            timeout=None,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(data)
```

## 数据源配置

### 云南网爬虫（yunnan_net）

**数据源**: 云南网（云南日报官网）站内搜索

**搜索地址**: `https://ynsearch.yunnan.cn/m_fullsearch/searchurl/mfullsearch!descResult.do`

**默认关键词**（地点 + 灾害类型）：

```
云南 地震
云南 洪水
云南 暴雨
云南 山体滑坡
云南 泥石流
云南 森林火灾
云南 干旱
云南 冰雹
云南 灾害
昆明 地震
昭通 洪涝
曲靖 灾害
丽江 滑坡
普洱 地震
大理 地震
```

**配置方式**：在 `.env` 文件中设置：

```env
ENABLE_YUNNAN_NET_CRAWLER=true
YUNNAN_NET_KEYWORDS=云南 地震,云南 洪水,昆明 地震,昭通 洪涝
```

**手动触发**：

```bash
# 触发云南网爬虫
curl -X POST http://127.0.0.1:8000/api/v1/crawler/run/yunnan_net
```

**数据字段提取能力**：
- 标题、正文内容、来源URL
- 灾害类型自动识别（地震/洪水/滑坡/火灾等）
- 云南16州市地名自动提取 + 经纬度
- 严重程度智能判断（基于关键词）
- 受影响人数、伤亡人数、经济损失自动提取
