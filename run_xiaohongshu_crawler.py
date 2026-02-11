#!/usr/bin/env python3
"""
小红书爬虫启动脚本
"""

import sys
import os
import logging

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.log import configure_logging
from scrapy.utils.log import configure_logging

from src.crawler.xiaohongshu.settings import get_scrapy_settings

def main():
    """主函数"""
    print("🕷️ 小红书爬虫启动中...")
    
    try:
        # 获取设置
        settings = get_scrapy_settings()
        
        # 配置日志
        configure_logging(settings)
        logging.getLogger('scrapy').setLevel(logging.INFO)
        
        # 创建爬虫进程
        process = CrawlerProcess(settings)
        
        # 添加爬虫
        process.crawl('xiaohongshu_note')
        process.crawl('xiaohongshu_user')
        process.crawl('xiaohongshu_comment')
        
        print("✅ 爬虫启动成功！")
        print("📝 日志文件: ./logs/xiaohongshu.log")
        print("🛑 按 Ctrl+C 停止爬虫")
        
        # 启动爬虫
        process.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ 爬虫已停止")
    except Exception as e:
        print(f"❌ 爬虫启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()