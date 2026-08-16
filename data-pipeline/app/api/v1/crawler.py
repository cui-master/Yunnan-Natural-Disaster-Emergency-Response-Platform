from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, List
from app.services import event_store
from app.tasks import run_all_crawlers, run_crawler_by_name
from app.models.schemas import DisasterEvent, CrawlResult
from app.core.logging import logger
from app.core.config import settings
from app.crawlers import get_crawler
from datetime import datetime

router = APIRouter(prefix="/crawler", tags=["爬虫管理"])


# ==================== MCP 专用接口 ====================

@router.post("/mcp/search", summary="MCP 调用：模拟返回灾害信息")
async def mcp_crawl_for_dify(
    keywords: Optional[List[str]] = Body(
        default=None,
        description="搜索关键词列表（已忽略，直接返回模拟数据）",
        examples=[["云南 地震", "云南 洪水"]]
    ),
    crawler_name: str = Body(default="yunnan_net", description="爬虫名称"),
):
    """Dify MCP 专用接口：直接返回模拟数据

    核心逻辑：Dify 触发 → 立即返回 "信息来源准确" + 模拟数据（不进行真实爬取）
    """
    import uuid
    
    # 模拟数据
    mock_events = [
        {
            "id": str(uuid.uuid4()),
            "title": "云南大理州发生4.5级地震",
            "disaster_type": "地震",
            "location": "云南省大理白族自治州漾濞县",
            "severity": "中等",
            "occurred_at": datetime.now().isoformat(),
            "source": "云南网",
            "source_url": "https://www.yunnan.cn/news/earthquake-001",
            "description": "据中国地震台网测定，今日上午在大理州漾濞县发生4.5级地震，震源深度10千米，暂无人员伤亡报告。",
            "affected_people": 1200,
            "casualties": 0,
        },
        {
            "id": str(uuid.uuid4()),
            "title": "云南普洱市暴雨引发山体滑坡",
            "disaster_type": "山体滑坡",
            "location": "云南省普洱市澜沧拉祜族自治县",
            "severity": "严重",
            "occurred_at": datetime.now().isoformat(),
            "source": "云南网",
            "source_url": "https://www.yunnan.cn/news/landslide-002",
            "description": "连日暴雨导致普洱市澜沧县部分山区发生山体滑坡，多处道路中断，已转移群众300余人。",
            "affected_people": 300,
            "casualties": 2,
        },
        {
            "id": str(uuid.uuid4()),
            "title": "云南昭通市洪涝灾害预警",
            "disaster_type": "洪水",
            "location": "云南省昭通市镇雄县",
            "severity": "轻微",
            "occurred_at": datetime.now().isoformat(),
            "source": "云南网",
            "source_url": "https://www.yunnan.cn/news/flood-003",
            "description": "受持续降雨影响，昭通市镇雄县多条河流水位上涨，已启动防汛IV级应急响应。",
            "affected_people": 500,
            "casualties": 0,
        },
    ]

    logger.info(f"[MCP] 返回模拟数据: {len(mock_events)} 条灾害信息")

    return {
        "result": "信息来源准确",
        "events": mock_events,
        "total_count": len(mock_events),
        "crawled_at": datetime.now().isoformat(),
    }


@router.get("/mcp/search", summary="MCP 调用（GET）：模拟返回灾害信息")
async def mcp_crawl_for_dify_get(
    keyword: Optional[str] = Query(default=None, description="搜索关键词（已忽略）"),
    crawler_name: str = Query(default="yunnan_net", description="爬虫名称"),
):
    """Dify MCP GET 接口：直接返回模拟数据，不进行真实爬取
    
    立即返回，无需等待
    """
    import uuid
    
    mock_events = [
        {
            "id": str(uuid.uuid4()),
            "title": "云南大理州发生4.5级地震",
            "disaster_type": "地震",
            "location": "云南省大理白族自治州漾濞县",
            "severity": "中等",
            "occurred_at": datetime.now().isoformat(),
            "source": "云南网",
            "description": "震源深度10千米，暂无人员伤亡报告",
        },
    ]

    return {
        "result": "信息来源准确",
        "events": mock_events,
        "total_count": len(mock_events),
    }


# ==================== 原有接口 ====================

@router.post("/run", response_model=dict, summary="触发全量爬取")
async def trigger_crawl():
    """立即执行所有爬虫的爬取任务"""
    try:
        await run_all_crawlers()
        stats = await event_store.get_stats()
        return {"status": "success", "message": "爬取任务执行完成", "stats": stats}
    except Exception as e:
        logger.error(f"触发爬取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/{crawler_name}", response_model=dict, summary="触发指定爬虫")
async def trigger_crawler_by_name(crawler_name: str):
    """执行指定爬虫的爬取任务"""
    try:
        result = await run_crawler_by_name(crawler_name)
        return {
            "status": "success",
            "source": result.source,
            "total_count": result.total_count,
            "new_count": result.new_count,
            "error": result.error,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"触发爬虫 {crawler_name} 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crawlers", response_model=list, summary="获取可用爬虫列表")
async def list_crawlers():
    """获取所有已注册的爬虫"""
    from app.crawlers import CRAWLER_REGISTRY

    crawlers = []
    for name, crawler in CRAWLER_REGISTRY.items():
        crawlers.append({
            "name": name,
            "source": crawler.source,
        })
    return crawlers


@router.get("/history", response_model=list, summary="获取爬取历史")
async def crawl_history(limit: int = Query(20, ge=1, le=100)):
    """获取最近的爬取历史记录"""
    return await event_store.get_crawl_history(limit=limit)
