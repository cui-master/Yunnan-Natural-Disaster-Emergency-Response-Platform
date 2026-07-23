from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from app.services import event_store
from app.tasks import run_all_crawlers, run_crawler_by_name
from app.models.schemas import DisasterEvent, CrawlResult
from app.core.logging import logger

router = APIRouter(prefix="/crawler", tags=["爬虫管理"])


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
