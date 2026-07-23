from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api import api_router
from app.tasks import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("服务已停止")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="云南省自然灾害应急决策平台 —— 数据管道服务（爬虫 + SSE 实时推送），为 Dify 工作流提供实时灾害数据",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["健康检查"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "sse_endpoint": "/api/v1/sse",
        "api_docs": "/docs",
    }


@app.get("/health", tags=["健康检查"])
async def health():
    return {"status": "ok"}


@app.get("/sse", tags=["SSE"], include_in_schema=False)
async def sse_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/sse")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
