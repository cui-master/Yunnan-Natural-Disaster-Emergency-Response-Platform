import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import settings
from app.core.logging import logger
from app.crawlers import get_all_crawlers
from app.services import event_store, sse_manager


scheduler: AsyncIOScheduler | None = None


async def run_all_crawlers():
    """运行所有爬虫"""
    logger.info("开始执行定时爬取任务...")

    crawlers = get_all_crawlers()
    for crawler in crawlers:
        try:
            result = await crawler.crawl()
            new_count = await event_store.add_events(result.events, result.source)
            result.new_count = new_count
            await event_store.record_crawl(result)

            result_dict = {
                "source": result.source,
                "total_count": result.total_count,
                "new_count": result.new_count,
                "error": result.error,
                "crawled_at": result.crawled_at.isoformat(),
            }
            await sse_manager.broadcast_crawl_result(result_dict)

            for event in result.events:
                await sse_manager.broadcast_new_event(event)

            logger.info(
                f"[{crawler.name}] 爬取完成: 共 {result.total_count} 条，新增 {new_count} 条"
            )
        except Exception as e:
            logger.error(f"[{crawler.name}] 爬取异常: {e}")

    logger.info("定时爬取任务执行完毕")


async def run_crawler_by_name(name: str):
    """运行指定爬虫"""
    from app.crawlers import get_crawler

    crawler = get_crawler(name)
    if not crawler:
        raise ValueError(f"爬虫 {name} 不存在")

    result = await crawler.crawl()
    new_count = await event_store.add_events(result.events, result.source)
    result.new_count = new_count
    await event_store.record_crawl(result)

    result_dict = {
        "source": result.source,
        "total_count": result.total_count,
        "new_count": result.new_count,
        "error": result.error,
        "crawled_at": result.crawled_at.isoformat(),
    }
    await sse_manager.broadcast_crawl_result(result_dict)

    for event in result.events:
        await sse_manager.broadcast_new_event(event)

    return result


async def keepalive_task():
    """SSE 心跳保活任务"""
    while True:
        try:
            if sse_manager.client_count > 0:
                await sse_manager.broadcast_keepalive()
                logger.debug(f"发送 SSE 心跳，当前连接数: {sse_manager.client_count}")
        except Exception as e:
            logger.error(f"心跳任务异常: {e}")
        await asyncio.sleep(settings.SSE_KEEPALIVE_INTERVAL)


def start_scheduler():
    """启动调度器"""
    global scheduler
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    scheduler.add_job(
        run_all_crawlers,
        trigger=IntervalTrigger(minutes=settings.CRAWLER_INTERVAL_MINUTES),
        id="crawl_all",
        name="全量爬取任务",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"调度器已启动，爬取间隔: {settings.CRAWLER_INTERVAL_MINUTES} 分钟")

    loop = asyncio.get_event_loop()
    loop.create_task(keepalive_task())


def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("调度器已停止")
