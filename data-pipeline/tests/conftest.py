"""pytest 公共配置与 fixture

环境变量（可在 .env 或系统环境设置）：
  DIFY_BASE_URL              Dify 服务地址，默认 http://localhost:8080
  DIFY_API_KEY_WORKFLOW      Workflow App API Key
  DIFY_API_KEY_DATASET       知识库 API Key
  FASTAPI_BASE_URL           本服务（data-pipeline）地址，默认 http://localhost:8000
  SPRING_BOOT_BASE_URL       Spring Boot 后端地址，默认 http://localhost:8083
  NEO4J_URI                  Neo4j bolt 地址，默认 bolt://localhost:7687
  NEO4J_USER / NEO4J_PASSWORD
  RUN_INTEGRATION            设为 1 时跑集成测试，否则只跑单元/mock 测试

使用：
  pytest tests/                          # 仅跑单元测试
  RUN_INTEGRATION=1 pytest tests/ -v     # 跑全部含集成测试
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# 把项目根目录加入 sys.path，方便 import app.*
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ============ 环境配置 ============

DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://localhost:8080")
DIFY_API_KEY_WORKFLOW = os.getenv("DIFY_API_KEY_WORKFLOW", "")
DIFY_API_KEY_DATASET = os.getenv("DIFY_API_KEY_DATASET", "")
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
SPRING_BOOT_BASE_URL = os.getenv("SPRING_BOOT_BASE_URL", "http://localhost:8083/api")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")

RUN_INTEGRATION = os.getenv("RUN_INTEGRATION", "0") == "1"


# ============ 跳过标记 ============

integration = pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason="集成测试需要 RUN_INTEGRATION=1 且依赖 Dify/Neo4j/Spring Boot 服务运行",
)


# ============ Fixtures ============

@pytest.fixture(scope="session")
def dify_config() -> Dict[str, str]:
    return {
        "base_url": DIFY_BASE_URL,
        "api_key_workflow": DIFY_API_KEY_WORKFLOW,
        "api_key_dataset": DIFY_API_KEY_DATASET,
    }


@pytest.fixture(scope="session")
def fastapi_base() -> str:
    return FASTAPI_BASE_URL


@pytest.fixture(scope="session")
def spring_boot_base() -> str:
    return SPRING_BOOT_BASE_URL


@pytest.fixture(scope="session")
def neo4j_config() -> Dict[str, str]:
    return {"uri": NEO4J_URI, "user": NEO4J_USER, "password": NEO4J_PASSWORD}


@pytest.fixture
def http_client():
    """同步 HTTP 客户端"""
    import httpx
    with httpx.Client(timeout=60) as client:
        yield client


@pytest.fixture
def async_http_client():
    """异步 HTTP 客户端"""
    import httpx
    with httpx.AsyncClient(timeout=60) as client:
        yield client


@pytest.fixture
def sample_incident_text() -> str:
    """事件抽取样例文本"""
    return (
        "2025年7月20日上午8点30分，云南省昭通市彝良县发生5.2级地震，"
        "震源深度10公里。据初步统计，受灾人口约2500人，部分房屋出现开裂倒塌，"
        "灾情等级为较大。目前已有消防救援队伍赶赴现场，但仍需医疗和物资支援。"
    )


@pytest.fixture
def sample_plan_content() -> str:
    """方案审查样例"""
    return (
        "## 彝良县5.2级地震应急方案\n"
        "1. 立即调派云南省消防救援总队200人赶赴现场\n"
        "2. 调派云南省医疗应急救援队50人建立临时医疗点\n"
        "3. 调拨帐篷500顶、棉被2000床、方便食品5000份\n"
        "4. 设立3个临时安置点，转移安置受灾群众2500人\n"
        "5. 启动道路抢修，确保救援通道畅通\n"
    )


# ============ 辅助函数 ============

def require_service(url: str, timeout: float = 3.0) -> bool:
    """检查服务是否可达"""
    import httpx
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            return resp.status_code < 500
    except Exception:
        return False
