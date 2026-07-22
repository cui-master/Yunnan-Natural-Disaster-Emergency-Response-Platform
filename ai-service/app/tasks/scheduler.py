from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import settings
from app.core.logging import logger
from app.pipeline import data_pipeline

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def _run_pipeline_job():
    """定时任务：执行完整数据管线"""
    logger.info("[定时任务] 开始执行数据管线...")
    try:
        result = await data_pipeline.run_full_pipeline(trigger_dify=False)
        logger.info(
            f"[定时任务] 管线执行完成：状态={result.get('status')}, "
            f"耗时={result.get('duration_seconds', 0)}s, "
            f"高风险区域={result.get('stats', {}).get('high_risk_areas', 0)}"
        )
    except Exception as e:
        logger.error(f"[定时任务] 管线执行异常: {e}")


def start_scheduler():
    scheduler.add_job(
        _run_pipeline_job,
        trigger=IntervalTrigger(minutes=settings.RISK_LEVEL_SYNC_INTERVAL_MINUTES),
        id="full_data_pipeline",
        name="完整数据管线（采集→校验→融合→研判→Neo4j更新）",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"定时任务已启动：完整数据管线（每 {settings.RISK_LEVEL_SYNC_INTERVAL_MINUTES} 分钟）"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务已停止")
