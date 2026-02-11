import os
from scrapy.utils.project import get_project_settings

class XiaohongshuSettings:
    """小红书爬虫配置"""
    
    # 请求配置
    DOWNLOAD_DELAY = 2
    RANDOMIZE_DOWNLOAD_DELAY = True
    CONCURRENT_REQUESTS = 4
    CONCURRENT_REQUESTS_PER_DOMAIN = 2
    
    # 下载超时
    DOWNLOAD_TIMEOUT = 30
    
    # 重试配置
    RETRY_TIMES = 3
    RETRY_HTTP_CODES = [500, 502, 503, 504, 408]
    
    # User-Agent配置
    USER_AGENT = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    # 禁用cookies
    COOKIES_ENABLED = False
    
    # 保存到文件的设置
    FEED_EXPORTERS = {
        'json': 'scrapy.exporters.JsonItemExporter',
        'jsonlines': 'scrapy.exporters.JsonLinesItemExporter',
    }
    
    # 管道设置
    ITEM_PIPELINES = {
        'social_content_creator.crawler.xiaohongshu.pipelines.XiaohongshuPipeline': 300,
    }
    
    # 数据库连接配置
    POSTGRESQL_URL = os.getenv('POSTGRESQL_URL', 'postgresql://localhost:5432/social_content')
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/social_content')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # 爬虫配置
    CRAWL_TIMEOUT = 3600 * 3  # 3小时
    MAX_PAGES_PER_DOMAIN = 1000
    LOG_LEVEL = 'INFO'
    LOG_FILE = './logs/xiaohongshu.log'
    
    # 代理配置
    PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
    PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []
    
    # 反爬虫配置
    CUSTOM_SETTINGS = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 60,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'HTTPERROR_ALLOW_ALL': False,
    }

# 获取Scrapy设置
def get_scrapy_settings():
    settings = get_project_settings()
    settings.set('BOT_NAME', 'social_content_crawler')
    settings.set('SPIDER_MODULES', ['social_content_creator.crawler.xiaohongshu.spiders'])
    settings.set('NEWSPIDER_MODULE', 'social_content_creator.crawler.xiaohongshu.spiders')
    
    # 应用小红书配置
    xiaohongshu_settings = XiaohongshuSettings()
    for key, value in vars(xiaohongshu_settings).items():
        if not key.startswith('_') and key.isupper():
            settings.set(key, value)
    
    return settings