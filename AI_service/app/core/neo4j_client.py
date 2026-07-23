from neo4j import GraphDatabase, AsyncGraphDatabase, Driver, AsyncDriver
from app.core.config import settings
from app.core.logging import logger
from contextlib import asynccontextmanager
from typing import AsyncGenerator


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
            return records

    @classmethod
    def execute_query_sync(cls, query: str, parameters: dict | None = None) -> list[dict]:
        if not cls._driver:
            raise RuntimeError("Neo4j 未初始化")
        with cls._driver.session(database=settings.NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return result.data()


neo4j_manager = Neo4jManager()
