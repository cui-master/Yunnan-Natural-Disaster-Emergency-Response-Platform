from fastapi import APIRouter
from .graph_nodes import router as graph_router
from .dispatch import router as dispatch_router
from .workflow import router as workflow_router
from .pipeline import router as pipeline_router
from .knowledge_base import router as kb_router

v1_router = APIRouter()
v1_router.include_router(graph_router)
v1_router.include_router(dispatch_router)
v1_router.include_router(workflow_router)
v1_router.include_router(pipeline_router)
v1_router.include_router(kb_router)

__all__ = ["v1_router"]
