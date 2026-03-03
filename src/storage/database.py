"""数据库连接管理器"""
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

import asyncpg
from asyncpg import Pool

from src.config.manager import DatabaseConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置
        """
        self.config = config
        self._pool: Optional[Pool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """
        初始化数据库连接池
        
        Returns:
            是否初始化成功
        """
        try:
            async with self._lock:
                if self._pool is not None:
                    logger.warning("database_already_initialized")
                    return True
                
                logger.info(
                    "initializing_database_pool",
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database
                )
                
                self._pool = await asyncpg.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    min_size=1,
                    max_size=self.config.pool_size,
                    command_timeout=60
                )
                
                # 测试连接
                async with self._pool.acquire() as conn:
                    version = await conn.fetchval('SELECT version()')
                    logger.info("database_connected", version=version)
                
                return True
                
        except Exception as e:
            logger.error("database_initialization_error", error=str(e))
            return False
    
    async def close(self) -> None:
        """关闭数据库连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("database_pool_closed")
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """
        获取数据库连接（上下文管理器）
        
        Yields:
            数据库连接
        """
        if not self._pool:
            raise RuntimeError("数据库连接池未初始化")
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args) -> str:
        """
        执行SQL语句（INSERT, UPDATE, DELETE）
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            执行结果状态
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """
        查询多行数据
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            查询结果列表
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        查询单行数据
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            查询结果记录，如果没有结果则返回None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """
        查询单个值
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            查询结果值
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_many(self, query: str, args_list: list) -> None:
        """
        批量执行SQL语句
        
        Args:
            query: SQL查询语句
            args_list: 参数列表
        """
        async with self.acquire() as conn:
            await conn.executemany(query, args_list)
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._pool is not None


class MySQLDatabaseManager(DatabaseManager):
    """MySQL数据库管理器（预留，暂未实现）"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        raise NotImplementedError("MySQL支持尚未实现，请使用PostgreSQL")
