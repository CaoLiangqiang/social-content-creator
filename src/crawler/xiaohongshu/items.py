# 条件导入Scrapy相关模块，避免测试环境中的依赖问题
try:
    import scrapy
    SCRAPY_AVAILABLE = True
except ImportError:
    SCRAPY_AVAILABLE = False
    # 创建模拟的scrapy模块
    class scrapy:
        class Item:
            pass
        class Field:
            pass

from typing import Dict, List, Optional
import re
import json

# 条件导入基础组件
try:
    from ..base.base_crawler import BaseCrawler
    from ..utils.logger import logger
except ImportError:
    # 创建模拟的基础组件
    class BaseCrawler:
        pass
    logger = None

if SCRAPY_AVAILABLE:
    class XiaohongshuNoteItem(scrapy.Item):
        """小红书笔记数据模型"""
        title = scrapy.Field()
        content = scrapy.Field()
        author = scrapy.Field()
        author_id = scrapy.Field()
        note_id = scrapy.Field()
        likes = scrapy.Field()
        comments = scrapy.Field()
        shares = scrapy.Field()
        tags = scrapy.Field()
        images = scrapy.Field()
        publish_time = scrapy.Field()
        crawl_time = scrapy.Field()
        url = scrapy.Field()

    class XiaohongshuUserItem(scrapy.Item):
        """小红书用户数据模型"""
        username = scrapy.Field()
        user_id = scrapy.Field()
        followers = scrapy.Field()
        following = scrapy.Field()
        notes_count = scrapy.Field()
        bio = scrapy.Field()
        avatar = scrapy.Field()
        cover_image = scrapy.Field()
        is_verified = scrapy.Field()
        crawl_time = scrapy.Field()
        url = scrapy.Field()

    class XiaohongshuCommentItem(scrapy.Item):
        """小红书评论数据模型"""
        comment_id = scrapy.Field()
        content = scrapy.Field()
        author = scrapy.Field()
        author_id = scrapy.Field()
        likes = scrapy.Field()
        publish_time = scrapy.Field()
        parent_id = scrapy.Field()
        reply_count = scrapy.Field()
        crawl_time = scrapy.Field()
        note_url = scrapy.Field()
else:
    # 创建不依赖Scrapy的数据模型
    class XiaohongshuNoteItem:
        """小红书笔记数据模型"""
        def __init__(self):
            self.title = None
            self.content = None
            self.author = None
            self.author_id = None
            self.note_id = None
            self.likes = None
            self.comments = None
            self.shares = None
            self.tags = []
            self.images = []
            self.publish_time = None
            self.crawl_time = None
            self.url = None
        
        def to_dict(self):
            return {k: v for k, v in self.__dict__.items()}

    class XiaohongshuUserItem:
        """小红书用户数据模型"""
        def __init__(self):
            self.username = None
            self.user_id = None
            self.followers = None
            self.following = None
            self.notes_count = None
            self.bio = None
            self.avatar = None
            self.cover_image = None
            self.is_verified = False
            self.crawl_time = None
            self.url = None
        
        def to_dict(self):
            return {k: v for k, v in self.__dict__.items()}

    class XiaohongshuCommentItem:
        """小红书评论数据模型"""
        def __init__(self):
            self.comment_id = None
            self.content = None
            self.author = None
            self.author_id = None
            self.likes = None
            self.publish_time = None
            self.parent_id = None
            self.reply_count = None
            self.crawl_time = None
            self.note_url = None
        
        def to_dict(self):
            return {k: v for k, v in self.__dict__.items()}