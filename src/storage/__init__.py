"""
数据存储模块

提供PostgreSQL和MongoDB的访问接口
"""

from .database import DatabaseManager, get_db_manager, init_database, close_database
from .dao import content_dao, user_dao, crawler_job_dao
from .mongodb import MongoDBManager, get_mongo_manager, init_mongodb, close_mongodb
from .pipeline import DataPipeline, CrawlerJobPipeline, data_pipeline, job_pipeline

__all__ = [
    # Database
    'DatabaseManager',
    'get_db_manager',
    'init_database',
    'close_database',
    
    # DAO
    'content_dao',
    'user_dao',
    'crawler_job_dao',
    
    # MongoDB
    'MongoDBManager',
    'get_mongo_manager',
    'init_mongodb',
    'close_mongodb',
    
    # Pipeline
    'DataPipeline',
    'CrawlerJobPipeline',
    'data_pipeline',
    'job_pipeline'
]
