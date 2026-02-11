"""
小红书爬虫测试

用于测试爬虫功能和验证数据质量
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.crawler.xiaohongshu import XiaohongshuCrawler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_keyword_search():
    """测试关键词搜索"""
    print("\n" + "="*60)
    print("测试：关键词搜索")
    print("="*60)
    
    crawler = XiaohongshuCrawler()
    
    # 搜索关键词
    keyword = "美食"
    results = await crawler.crawl_by_keyword(keyword, limit=10)
    
    print(f"\n搜索结果：找到 {len(results)} 条笔记")
    
    # 显示前3条
    for i, note in enumerate(results[:3], 1):
        print(f"\n--- 笔记 {i} ---")
        print(f"标题: {note['title']}")
        print(f"作者: {note['author_name']}")
        print(f"点赞: {note['like_count']}")
        print(f"收藏: {note['collect_count']}")
        print(f"链接: {note['url']}")
    
    # 显示统计
    stats = crawler.get_stats()
    print(f"\n爬虫统计：{stats}")


async def test_content_detail():
    """测试笔记详情爬取"""
    print("\n" + "="*60)
    print("测试：笔记详情")
    print("="*60)
    
    crawler = XiaohongshuCrawler()
    
    # 笔记ID（需要替换为真实ID）
    content_id = "64f1a6d7000000001e01b8d8"  # 示例ID
    
    print(f"\n爬取笔记详情：{content_id}")
    detail = await crawler.crawl_content_detail(content_id)
    
    if detail:
        print(f"\n标题: {detail['title']}")
        print(f"作者: {detail['author_name']}")
        print(f"内容: {detail['content'][:100]}...")
        print(f"图片数量: {len(detail['images'])}")
        print(f"标签: {', '.join(detail['tags'][:5])}")
    else:
        print("获取失败")


async def test_user_info():
    """测试用户信息爬取"""
    print("\n" + "="*60)
    print("测试：用户信息")
    print("="*60)
    
    crawler = XiaohongshuCrawler()
    
    # 用户ID（需要替换为真实ID）
    user_id = "5f1e7b2e0000000001005c36"  # 示例ID
    
    print(f"\n爬取用户信息：{user_id}")
    user_info = await crawler.crawl_user_info(user_id)
    
    if user_info:
        print(f"\n用户名: {user_info['username']}")
        print(f"简介: {user_info['bio'][:100]}...")
        print(f"粉丝: {user_info['follower_count']}")
        print(f"关注: {user_info['following_count']}")
        print(f"笔记数: {user_info['note_count']}")
    else:
        print("获取失败")


async def test_comments():
    """测试评论爬取"""
    print("\n" + "="*60)
    print("测试：评论爬取")
    print("="*60)
    
    crawler = XiaohongshuCrawler()
    
    # 笔记ID（需要替换为真实ID）
    content_id = "64f1a6d7000000001e01b8d8"  # 示例ID
    
    print(f"\n爬取评论：{content_id}")
    comments = await crawler.crawl_comments(content_id, limit=20)
    
    print(f"\n获取到 {len(comments)} 条评论")
    
    # 显示前5条
    for i, comment in enumerate(comments[:5], 1):
        print(f"\n--- 评论 {i} ---")
        print(f"用户: {comment['username']}")
        print(f"内容: {comment['content'][:100]}...")
        print(f"点赞: {comment['like_count']}")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("小红书爬虫测试套件")
    print("="*60)
    
    # 注意：这些测试需要：
    # 1. 网络连接
    # 2. 有效的Cookie（如果需要）
    # 3. 真实的内容ID和用户ID
    
    # 如果没有配置Cookie，大部分请求会被限制
    print("\n⚠️  注意：")
    print("1. 这些测试需要有效的Cookie才能成功")
    print("2. 示例ID需要替换为真实的笔记/用户ID")
    print("3. 没有Cookie时，大部分请求会被小红书限制")
    print("\n当前跳过实际测试，仅展示测试框架")
    
    # TODO: 实际运行测试时取消注释
    # await test_keyword_search()
    # await test_content_detail()
    # await test_user_info()
    # await test_comments()
    
    print("\n测试框架已就绪，配置Cookie后可运行实际测试")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(run_all_tests())
