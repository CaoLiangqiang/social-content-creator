"""
MongoDB连接管理

用于存储爬虫原始数据
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class MongoDBManager:
    """
    MongoDB管理器
    
    用于存储爬虫原始数据
    """
    
    def __init__(
        self,
        uri: str = 'mongodb://localhost:27017',
        database: str = 'social_content_creator'
    ):
        """
        初始化MongoDB管理器
        
        Args:
            uri: MongoDB连接URI
            database: 数据库名称
        """
        self.uri = uri
        self.database_name = database
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """连接MongoDB"""
        try:
            self._client = AsyncIOMotorClient(self.uri)
            self._db = self._client[self.database_name]
            
            # 测试连接
            await self._client.admin.command('ping')
            
            logger.info(f"✅ MongoDB connected: {self.uri}/{self.database_name}")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            raise
    
    async def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """获取数据库实例"""
        if not self._db:
            raise RuntimeError("MongoDB not connected")
        return self._db
    
    async def insert_raw_data(
        self,
        collection: str,
        platform: str,
        data_type: str,
        raw_html: str = '',
        raw_json: Dict = None,
        metadata: Dict = None
    ) -> str:
        """
        插入原始爬虫数据
        
        Args:
            collection: 集合名称
            platform: 平台名称
            data_type: 数据类型（note, video, user等）
            raw_html: 原始HTML
            raw_json: 原始JSON
            metadata: 元数据
            
        Returns:
            插入的文档ID
        """
        doc = {
            'platform': platform,
            'data_type': data_type,
            'raw_html': raw_html,
            'raw_json': raw_json or {},
            'metadata': metadata or {},
            'processed': False,
            'created_at': datetime.now()
        }
        
        result = await self.db[collection].insert_one(doc)
        
        logger.debug(f"Raw data inserted: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def find_unprocessed(
        self,
        collection: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        查找未处理的原始数据
        
        Args:
            collection: 集合名称
            limit: 返回数量
            
        Returns:
            文档列表
        """
        cursor = self.db[collection].find(
            {'processed': False}
        ).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return docs
    
    async def mark_processed(self, collection: str, doc_id: str):
        """
        标记数据为已处理
        
        Args:
            collection: 集合名称
            doc_id: 文档ID
        """
        from bson.objectid import ObjectId
        
        await self.db[collection].update_one(
            {'_id': ObjectId(doc_id)},
            {'$set': {'processed': True}}
        )
    
    async def save_snapshot(
        self,
        content_id: str,
        platform: str,
        platform_content_id: str,
        snapshot_data: Dict
    ) -> str:
        """
        保存内容快照
        
        Args:
            content_id: PostgreSQL中的内容ID
            platform: 平台名称
            platform_content_id: 平台内容ID
            snapshot_data: 快照数据
            
        Returns:
            文档ID
        """
        doc = {
            'content_id': content_id,
            'platform': platform,
            'platform_content_id': platform_content_id,
            'snapshot_data': snapshot_data,
            'snapshot_time': datetime.now()
        }
        
        result = await self.db['content_snapshots'].insert_one(doc)
        return str(result.inserted_id)


# 全局MongoDB管理器实例
_mongo_manager: Optional[MongoDBManager] = None


def get_mongo_manager() -> MongoDBManager:
    """
    获取全局MongoDB管理器实例
    
    Returns:
        MongoDBManager实例
    """
    global _mongo_manager
    
    if _mongo_manager is None:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        database = os.getenv('MONGODB_DATABASE', 'social_content_creator')
        
        _mongo_manager = MongoDBManager(uri, database)
    
    return _mongo_manager


async def init_mongodb():
    """初始化MongoDB连接"""
    mongo = get_mongo_manager()
    await mongo.connect()


async def close_mongodb():
    """关闭MongoDB连接"""
    mongo = get_mongo_manager()
    await mongo.close()
