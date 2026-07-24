from fastapi import APIRouter
from .graph_nodes import router as graph_router
from .dispatch import router as dispatch_router
from .workflow import router as workflow_router
from .pipeline import router as pipeline_router
from .knowledge_base import router as kb_router
from .reporter import router as reporter_router
from .commander import router as commander_router
from .resource import router as resource_router
from .admin import router as admin_router

v1_router = APIRouter()
v1_router.include_router(graph_router)
v1_router.include_router(dispatch_router)
v1_router.include_router(workflow_router)
v1_router.include_router(pipeline_router)
v1_router.include_router(kb_router)
v1_router.include_router(reporter_router)
v1_router.include_router(commander_router)
v1_router.include_router(resource_router)
v1_router.include_router(admin_router)

__all__ = ["v1_router"]
