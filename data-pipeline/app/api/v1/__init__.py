from fastapi import APIRouter
from app.api.v1.sse_route import router as sse_router
from app.api.v1.events import router as events_router
from app.api.v1.crawler import router as crawler_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(sse_router)
api_router.include_router(events_router)
api_router.include_router(crawler_router)

__all__ = ["api_router"]
