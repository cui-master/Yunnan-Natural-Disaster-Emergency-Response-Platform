from neo4j import GraphDatabase, AsyncGraphDatabase, Driver, AsyncDriver
from app.core.config import settings
from app.core.logging import logger
from typing import Any


def _serialize_value(value: Any) -> Any:
    """递归转换 Neo4j 特殊类型为可 JSON 序列化的 Python 原生类型"""
    if hasattr(value, "iso_format") and callable(value.iso_format):
        return value.iso_format()
    if hasattr(value, "items") and callable(value.items):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


class Neo4jManager:
    _driver: Driver | None = None
    _async_driver: AsyncDriver | None = None

    @classmethod
    def _ensure_init(cls):
        """懒初始化/自动重连：如果 driver 不存在就初始化"""
        if cls._async_driver is None:
            cls.init()

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
            cls._driver = None
            cls._async_driver = None
            logger.error(f"Neo4j 连接失败: {e}")
            raise

    @classmethod
    def close(cls):
        if cls._driver:
            cls._driver.close()
        if cls._async_driver:
            cls._async_driver.close()
        cls._driver = None
        cls._async_driver = None
        logger.info("Neo4j 连接已关闭")

    @classmethod
    async def execute_query(cls, query: str, parameters: dict | None = None) -> list[dict]:
        cls._ensure_init()
        try:
            async with cls._async_driver.session(database=settings.NEO4J_DATABASE) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return [_serialize_value(r) for r in records]
        except Exception as e:
            # 查询失败可能是连接断开，尝试重连一次
            logger.warning(f"Neo4j查询失败，尝试重连: {e}")
            cls.close()
            cls.init()
            async with cls._async_driver.session(database=settings.NEO4J_DATABASE) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return [_serialize_value(r) for r in records]

    @classmethod
    def execute_query_sync(cls, query: str, parameters: dict | None = None) -> list[dict]:
        cls._ensure_init()
        try:
            with cls._driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run(query, parameters or {})
                records = result.data()
                return [_serialize_value(r) for r in records]
        except Exception as e:
            logger.warning(f"Neo4j同步查询失败，尝试重连: {e}")
            cls.close()
            cls.init()
            with cls._driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run(query, parameters or {})
                records = result.data()
                return [_serialize_value(r) for r in records]


neo4j_manager = Neo4jManager()
