from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.log import configure_logging
import logging

from .settings import get_scrapy_settings
from .pipelines import XiaohongshuPipeline

class XiaohongshuCrawler:
    """小红书爬虫管理器"""
    
    def __init__(self):
        self.settings = get_scrapy_settings()
        self.process = None
        
    def run(self):
        """运行爬虫"""
        try:
            # 配置日志
            configure_logging(self.settings)
            logging.getLogger('scrapy').setLevel(logging.INFO)
            
            # 创建爬虫进程
            self.process = CrawlerProcess(self.settings)
            
            # 添加爬虫
            self.process.crawl('xiaohongshu_note')
            self.process.crawl('xiaohongshu_user')
            
            # 启动爬虫
            self.process.start()
            
        except Exception as e:
            logging.error(f"爬虫运行失败: {str(e)}")
            raise

if __name__ == "__main__":
    crawler = XiaohongshuCrawler()
    crawler.run()