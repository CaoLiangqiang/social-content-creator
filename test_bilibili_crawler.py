"""
B站爬虫测试脚本

测试B站爬虫的各个功能模块
"""

import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawler.bilibili import (
    BilibiliCrawler,
    quick_crawl_video,
    quick_search_videos
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_video_crawl():
    """测试视频爬虫"""
    logger.info("=" * 50)
    logger.info("开始测试视频爬虫...")
    logger.info("=" * 50)
    
    # 使用一个公开的B站视频进行测试
    test_bvid = "BV1uv411q7Mv"  # 这是一个示例视频ID
    
    try:
        crawler = BilibiliCrawler()
        video_data = await crawler.crawl_video_full(test_bvid)
        
        logger.info(f"视频爬取结果:")
        logger.info(f"- BV号: {video_data.get('bvid')}")
        logger.info(f"- 视频信息: {'✓' if video_data.get('video_info') else '✗'}")
        logger.info(f"- 弹幕数量: {len(video_data.get('danmakus', []))}")
        logger.info(f"- 评论数量: {len(video_data.get('comments', []))}")
        logger.info(f"- UP主信息: {'✓' if video_data.get('author_info') else '✗'}")
        
        crawler.export_stats()
        return True
        
    except Exception as e:
        logger.error(f"视频爬取测试失败: {str(e)}")
        return False


async def test_search_videos():
    """测试视频搜索"""
    logger.info("=" * 50)
    logger.info("开始测试视频搜索...")
    logger.info("=" * 50)
    
    test_keyword = "人工智能"
    
    try:
        crawler = BilibiliCrawler()
        videos = await crawler.crawl_videos_by_keyword(
            keyword=test_keyword,
            limit=10,
            full_crawl=False
        )
        
        logger.info(f"搜索结果:")
        logger.info(f"- 搜索关键词: {test_keyword}")
        logger.info(f"- 找到视频: {len(videos)} 个")
        
        if videos:
            logger.info("- 前3个视频标题:")
            for i, video in enumerate(videos[:3], 1):
                logger.info(f"  {i}. {video.get('title', 'Unknown')}")
        
        crawler.export_stats()
        return True
        
    except Exception as e:
        logger.error(f"视频搜索测试失败: {str(e)}")
        return False


async def test_user_crawl():
    """测试UP主爬虫"""
    logger.info("=" * 50)
    logger.info("开始测试UP主爬虫...")
    logger.info("=" * 50)
    
    # 使用一个公开的UP主MID进行测试
    test_mid = "22659294"  # 这是一个示例UP主ID
    
    try:
        crawler = BilibiliCrawler()
        
        # 爬取UP主信息
        user_info = await crawler.user_spider.crawl_user_info_by_mid(test_mid)
        
        if user_info:
            logger.info(f"UP主信息:")
            logger.info(f"- MID: {user_info.get('mid')}")
            logger.info(f"- 昵称: {user_info.get('name')}")
            logger.info(f"- 等级: {user_info.get('level')}")
            logger.info(f"- 粉丝数: {user_info.get('follower_count')}")
            logger.info(f"- 视频数: {user_info.get('video_count')}")
        else:
            logger.warning("UP主信息爬取失败")
        
        # 爬取UP主视频列表
        user_videos = await crawler.crawl_user_videos(
            mid=test_mid,
            limit=10,
            full_crawl=False
        )
        
        logger.info(f"- 视频数量: {len(user_videos)}")
        
        if user_videos:
            logger.info("- 前3个视频:")
            for i, video in enumerate(user_videos[:3], 1):
                logger.info(f"  {i}. {video.get('title', 'Unknown')}")
        
        crawler.export_stats()
        return True
        
    except Exception as e:
        logger.error(f"UP主爬取测试失败: {str(e)}")
        return False


async def test_quick_functions():
    """测试便捷函数"""
    logger.info("=" * 50)
    logger.info("开始测试便捷函数...")
    logger.info("=" * 50)
    
    try:
        # 测试快速爬取视频
        logger.info("测试 quick_crawl_video...")
        video = await quick_crawl_video("BV1uv411q7Mv")
        logger.info(f"快速爬取视频: {'✓' if video else '✗'}")
        
        # 测试快速搜索视频
        logger.info("测试 quick_search_videos...")
        videos = await quick_search_videos("编程", limit=5)
        logger.info(f"快速搜索视频: 找到 {len(videos)} 个视频")
        
        return True
        
    except Exception as e:
        logger.error(f"便捷函数测试失败: {str(e)}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始B站爬虫测试")
    logger.info(f"测试时间: {datetime.now().isoformat()}")
    logger.info("")
    
    test_results = []
    
    # 测试视频爬取
    result = await test_video_crawl()
    test_results.append(("视频爬取", result))
    logger.info("")
    
    # 测试视频搜索
    result = await test_search_videos()
    test_results.append(("视频搜索", result))
    logger.info("")
    
    # 测试UP主爬取
    result = await test_user_crawl()
    test_results.append(("UP主爬取", result))
    logger.info("")
    
    # 测试便捷函数
    result = await test_quick_functions()
    test_results.append(("便捷函数", result))
    logger.info("")
    
    # 汇总测试结果
    logger.info("=" * 50)
    logger.info("📊 测试结果汇总")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"- {test_name}: {status}")
    
    logger.info("")
    logger.info(f"总计: {passed}/{total} 测试通过")
    logger.info(f"成功率: {passed/total*100:.1f}%")
    logger.info(f"完成时间: {datetime.now().isoformat()}")
    
    if passed == total:
        logger.info("🎉 所有测试通过！")
    else:
        logger.warning(f"⚠️  {total - passed} 个测试失败")


def main():
    """主函数"""
    try:
        # 运行异步测试
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()