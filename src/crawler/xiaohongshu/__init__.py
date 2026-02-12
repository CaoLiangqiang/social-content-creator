# 条件导入Scrapy相关模块，避免测试环境中的依赖问题
try:
    from scrapy import signals
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from scrapy.log import configure_logging
    import logging
    
    SCRAPY_AVAILABLE = True
    
    def get_scrapy_crawler():
        """获取Scrapy爬虫实例（仅在Scrapy可用时）"""
        try:
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
            
            return XiaohongshuCrawler
            
        except ImportError:
            return None
            
except ImportError:
    SCRAPY_AVAILABLE = False
    get_scrapy_crawler = None

# 导入数据模型和设置（这些不依赖Scrapy）
from .items import XiaohongshuNoteItem, XiaohongshuUserItem, XiaohongshuCommentItem

if __name__ == "__main__":
    crawler = XiaohongshuCrawler()
    crawler.run()