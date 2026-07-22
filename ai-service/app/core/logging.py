from loguru import logger
import sys
from pathlib import Path

log_path = Path("logs")
log_path.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)
logger.add(
    log_path / "app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    encoding="utf-8",
    level="DEBUG",
)

__all__ = ["logger"]
