from neo4j import GraphDatabase, AsyncGraphDatabase, Driver, AsyncDriver
from app.core.config import settings
from app.core.logging import logger
from contextlib import asynccontextmanager
from typing import Any


def _serialize_value(value: Any) -> Any:
    """递归转换 Neo4j 特殊类型为可 JSON 序列化的 Python 原生类型

    处理 neo4j.time.DateTime / Date / Time / Duration / Node / Relationship 等。
    """
    # neo4j 时间类型都有 iso_format()
    if hasattr(value, "iso_format") and callable(value.iso_format):
        return value.iso_format()
    # neo4j Node / Relationship
    if hasattr(value, "items") and callable(value.items):
        return {k: _serialize_value(v) for k, v in value.items()}
    # 列表/元组
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    # dict
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


class Neo4jManager:
    _driver: Driver | None = None
    _async_driver: AsyncDriver | None = None

    @classmethod
    def init(cls):
        try:
            cls._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            cls._async_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            cls._driver.verify_connectivity()
            logger.info(f"Neo4j 连接成功: {settings.NEO4J_URI}")
        except Exception as e:
            logger.error(f"Neo4j 连接失败: {e}")
            raise

    @classmethod
    def close(cls):
        if cls._driver:
            cls._driver.close()
        if cls._async_driver:
            cls._async_driver.close()
        logger.info("Neo4j 连接已关闭")

    @classmethod
    async def execute_query(cls, query: str, parameters: dict | None = None) -> list[dict]:
        if not cls._async_driver:
            raise RuntimeError("Neo4j 未初始化")
        async with cls._async_driver.session(database=settings.NEO4J_DATABASE) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return [_serialize_value(r) for r in records]

    @classmethod
    def execute_query_sync(cls, query: str, parameters: dict | None = None) -> list[dict]:
        if not cls._driver:
            raise RuntimeError("Neo4j 未初始化")
        with cls._driver.session(database=settings.NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            records = result.data()
            return [_serialize_value(r) for r in records]


neo4j_manager = Neo4jManager()
