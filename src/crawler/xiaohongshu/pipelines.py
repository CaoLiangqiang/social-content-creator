import scrapy
import psycopg2
import pymongo
import redis
import json
from datetime import datetime
from typing import Dict, Any
from scrapy.exceptions import DropItem

from .utils.logger import logger
from .items import XiaohongshuNoteItem, XiaohongshuUserItem, XiaohongshuCommentItem

class XiaohongshuPipeline:
    """小红书爬虫数据处理管道"""
    
    def __init__(self, postgresql_url: str, mongodb_url: str, redis_url: str):
        self.postgresql_url = postgresql_url
        self.mongodb_url = mongodb_url
        self.redis_url = redis_url
        
        self.postgresql_conn = None
        self.mongodb_client = None
        self.mongodb_db = None
        self.redis_client = None
        
        self.processed_items = set()
    
    @classmethod
    def from_crawler(cls, crawler):
        """从crawler中获取配置"""
        return cls(
            postgresql_url=crawler.settings.get('POSTGRESQL_URL'),
            mongodb_url=crawler.settings.get('MONGODB_URL'),
            redis_url=crawler.settings.get('REDIS_URL')
        )
    
    def open_spider(self, spider):
        """爬虫启动时调用"""
        logger.info("初始化数据库连接...")
        
        # 初始化PostgreSQL连接
        try:
            self.postgresql_conn = psycopg2.connect(self.postgresql_url)
            logger.info("PostgreSQL连接成功")
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {str(e)}")
            raise
        
        # 初始化MongoDB连接
        try:
            self.mongodb_client = pymongo.MongoClient(self.mongodb_url)
            self.mongodb_db = self.mongodb_client['social_content']
            self.mongodb_db['original_data'].create_index([('crawl_time', -1)])
            logger.info("MongoDB连接成功")
        except Exception as e:
            logger.error(f"MongoDB连接失败: {str(e)}")
            raise
        
        # 初始化Redis连接
        try:
            self.redis_client = redis.from_url(self.redis_url)
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise
    
    def close_spider(self, spider):
        """爬虫关闭时调用"""
        logger.info("关闭数据库连接...")
        
        if self.postgresql_conn:
            self.postgresql_conn.close()
        
        if self.mongodb_client:
            self.mongodb_client.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("数据库连接已关闭")
    
    def process_item(self, item, spider):
        """处理爬取的item"""
        try:
            # 检查是否已处理（使用Redis去重）
            item_id = self._get_item_id(item)
            if self._is_processed(item_id):
                raise DropItem(f"Item已处理: {item_id}")
            
            # 根据item类型进行相应处理
            if isinstance(item, XiaohongshuNoteItem):
                self._process_note_item(item, spider)
            elif isinstance(item, XiaohongshuUserItem):
                self._process_user_item(item, spider)
            elif isinstance(item, XiaohongshuCommentItem):
                self._process_comment_item(item, spider)
            
            # 标记为已处理
            self._mark_processed(item_id)
            
            logger.info(f"处理成功: {item_id}")
            return item
            
        except Exception as e:
            logger.error(f"处理Item失败: {str(e)}")
            raise DropItem(f"Item处理失败: {str(e)}")
    
    def _get_item_id(self, item) -> str:
        """获取item的唯一ID"""
        if isinstance(item, XiaohongshuNoteItem):
            return f"xiaohongshu_note_{item.get('note_id', '')}"
        elif isinstance(item, XiaohongshuUserItem):
            return f"xiaohongshu_user_{item.get('user_id', '')}"
        elif isinstance(item, XiaohongshuCommentItem):
            return f"xiaohongshu_comment_{item.get('comment_id', '')}"
        else:
            return str(hash(str(item)))
    
    def _is_processed(self, item_id: str) -> bool:
        """检查item是否已处理"""
        return self.redis_client.sismember('processed_items', item_id)
    
    def _mark_processed(self, item_id: str):
        """标记item为已处理"""
        self.redis_client.sadd('processed_items', item_id)
    
    def _process_note_item(self, item: XiaohongshuNoteItem, spider):
        """处理笔记item"""
        # 转换字典格式
        note_data = dict(item)
        
        # 添加时间戳
        note_data['crawl_time'] = datetime.now()
        
        # 保存到PostgreSQL
        self._save_to_postgresql(note_data, 'contents')
        
        # 保存到MongoDB（原始数据）
        self._save_to_mongodb(note_data, 'xiaohongshu_notes')
        
        logger.info(f"笔记已保存: {note_data.get('note_id', '')}")
    
    def _process_user_item(self, item: XiaohongshuUserItem, spider):
        """处理用户item"""
        # 转换字典格式
        user_data = dict(item)
        
        # 添加时间戳
        user_data['crawl_time'] = datetime.now()
        
        # 保存到PostgreSQL
        self._save_to_postgresql(user_data, 'users')
        
        # 保存到MongoDB（原始数据）
        self._save_to_mongodb(user_data, 'xiaohongshu_users')
        
        logger.info(f"用户已保存: {user_data.get('user_id', '')}")
    
    def _process_comment_item(self, item: XiaohongshuCommentItem, spider):
        """处理评论item"""
        # 转换字典格式
        comment_data = dict(item)
        
        # 添加时间戳
        comment_data['crawl_time'] = datetime.now()
        
        # 保存到PostgreSQL
        self._save_to_postgresql(comment_data, 'comments')
        
        # 保存到MongoDB（原始数据）
        self._save_to_mongodb(comment_data, 'xiaohongshu_comments')
        
        logger.info(f"评论已保存: {comment_data.get('comment_id', '')}")
    
    def _save_to_postgresql(self, data: Dict, table_name: str):
        """保存到PostgreSQL"""
        try:
            cursor = self.postgresql_conn.cursor()
            
            # 构建字段列表和值列表
            columns = list(data.keys())
            values = [data.get(col) for col in columns]
            placeholders = ['%s'] * len(columns)
            
            # 构建SQL语句
            query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT (id) DO UPDATE SET
                {', '.join([f'{col} = EXCLUDED.{col}' for col in columns if col != 'id'])}
            """
            
            # 执行插入
            cursor.execute(query, values)
            self.postgresql_conn.commit()
            
        except Exception as e:
            self.postgresql_conn.rollback()
            logger.error(f"PostgreSQL保存失败: {str(e)}")
            raise
    
    def _save_to_mongodb(self, data: Dict, collection_name: str):
        """保存到MongoDB"""
        try:
            collection = self.mongodb_db[collection_name]
            collection.insert_one(data)
        except Exception as e:
            logger.error(f"MongoDB保存失败: {str(e)}")
            raise