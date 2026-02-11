"""
数据库连接管理

PostgreSQL连接池和会话管理
"""

import asyncio
from typing import AsyncGenerator, Optional
import asyncpg
from asyncpg import Pool, Connection
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库管理器
    
    管理PostgreSQL连接池和会话
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5432,
        database: str = 'social_content_creator',
        user: str = 'postgres',
        password: str = '',
        min_size: int = 5,
        max_size: int = 20
    ):
        """
        初始化数据库管理器
        
        Args:
            host: 数据库主机
            port: 数据库端口
            database: 数据库名称
            user: 用户名
            password: 密码
            min_size: 最小连接数
            max_size: 最大连接数
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        
        self._pool: Optional[Pool] = None
    
    async def create_pool(self):
        """创建连接池"""
        if self._pool:
            logger.warning("Pool already exists")
            return
        
        try:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )
            
            logger.info(
                f"Database pool created: {self.host}:{self.port}/{self.database} "
                f"(min={self.min_size}, max={self.max_size})"
            )
            
        except Exception as e:
            logger.error(f"Failed to create database pool: {str(e)}")
            raise
    
    async def close_pool(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
    
    async def get_connection(self) -> Connection:
        """
        获取数据库连接
        
        Returns:
            数据库连接对象
        """
        if not self._pool:
            await self.create_pool()
        
        return await self._pool.acquire()
    
    async def release_connection(self, connection: Connection):
        """
        释放数据库连接
        
        Args:
            connection: 连接对象
        """
        if self._pool:
            await self._pool.release(connection)
    
    async def execute(self, query: str, *args) -> str:
        """
        执行SQL语句（无返回值）
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            执行状态
        """
        async with await self.get_connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """
        执行查询并返回所有结果
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            查询结果列表
        """
        async with await self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        """
        执行查询并返回单行结果
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            查询结果字典或None
        """
        async with await self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """
        执行查询并返回单个值
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            查询结果值
        """
        async with await self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    def transaction(self):
        """
        获取事务上下文管理器
        
        Returns:
            事务对象
        """
        if not self._pool:
            raise RuntimeError("Pool not created")
        
        return self._pool.transaction()
    
    async def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            是否连接成功
        """
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    获取全局数据库管理器实例
    
    Returns:
        DatabaseManager实例
    """
    global _db_manager
    
    if _db_manager is None:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        _db_manager = DatabaseManager(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'social_content_creator'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
    
    return _db_manager


async def init_database():
    """初始化数据库连接池"""
    db = get_db_manager()
    await db.create_pool()
    
    # 测试连接
    if await db.test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")


async def close_database():
    """关闭数据库连接池"""
    db = get_db_manager()
    await db.close_pool()
