from scrapy.spiders import CrawlSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from typing import Dict, List, Optional
import re
import json

from ..base.base_crawler import BaseCrawler
from ..utils.logger import logger

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