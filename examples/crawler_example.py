"""
完整的爬虫示例

整合爬虫、数据存储、数据管道的完整示例
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.crawler.xiaohongshu import XiaohongshuCrawler
from src.storage import (
    init_database,
    init_mongodb,
    close_database,
    close_mongodb,
    crawler_job_dao,
    job_pipeline
)


async def crawl_keyword_example(keyword: str, limit: int = 50):
    """
    关键词爬取示例
    
    Args:
        keyword: 搜索关键词
        limit: 最大爬取数量
    """
    print(f"\n{'='*60}")
    print(f"开始爬取关键词: {keyword}")
    print(f"{'='*60}\n")
    
    # 1. 初始化数据库
    print("📦 初始化数据库连接...")
    await init_database()
    await init_mongodb()
    print("✅ 数据库连接成功\n")
    
    # 2. 创建爬虫任务
    print("📋 创建爬虫任务...")
    job_id = await crawler_job_dao.create_job(
        platform_id=1,  # 小红书
        job_type='keyword_search',
        target=keyword,
        max_items=limit
    )
    print(f"✅ 任务创建成功: {job_id}\n")
    
    # 3. 初始化爬虫
    print("🕷️ 初始化爬虫...")
    crawler = XiaohongshuCrawler()
    
    # 设置Cookie（如果有的话）
    # cookie = os.getenv('XIAOHONGSHU_COOKIE')
    # if cookie:
    #     crawler.set_cookie(cookie)
    #     print("✅ Cookie已设置")
    
    print("✅ 爬虫初始化完成\n")
    
    # 4. 定义爬虫函数
    async def crawl_func():
        print(f"🔍 开始搜索: {keyword}")
        contents = await crawler.crawl_by_keyword(keyword, limit=limit)
        print(f"✅ 搜索完成，找到 {len(contents)} 条笔记\n")
        return contents
    
    # 5. 执行任务
    print("🚀 执行爬虫任务...")
    try:
        await job_pipeline.execute_job(job_id, crawl_func)
    except Exception as e:
        print(f"❌ 任务执行失败: {str(e)}")
        return
    
    # 6. 显示结果
    print(f"\n{'='*60}")
    print("任务执行完成")
    print(f"{'='*60}\n")
    
    # 显示统计
    stats = crawler.get_stats()
    print(f"📊 爬虫统计:")
    print(f"  - 总请求数: {stats['total_requests']}")
    print(f"  - 成功请求: {stats['success_requests']}")
    print(f"  - 失败请求: {stats['failed_requests']}")
    print(f"  - 成功率: {stats['success_rate']}%")
    print(f"  - 运行时间: {stats['runtime_seconds']:.2f}秒")
    print(f"  - 请求速率: {stats['requests_per_second']:.2f} req/s\n")
    
    # 显示数据管道统计
    pipeline_stats = job_pipeline.data_pipeline.get_stats()
    print(f"📊 数据管道统计:")
    print(f"  - 总处理数: {pipeline_stats['total_processed']}")
    print(f"  - 成功数: {pipeline_stats['success_count']}")
    print(f"  - 失败数: {pipeline_stats['failed_count']}\n")
    
    # 7. 关闭数据库连接
    print("🔒 关闭数据库连接...")
    await close_database()
    await close_mongodb()
    print("✅ 完成\n")


async def crawl_content_detail_example(content_id: str):
    """
    爬取笔记详情示例
    
    Args:
        content_id: 笔记ID
    """
    print(f"\n{'='*60}")
    print(f"爬取笔记详情: {content_id}")
    print(f"{'='*60}\n")
    
    # 初始化数据库
    await init_database()
    await init_mongodb()
    
    # 初始化爬虫
    crawler = XiaohongshuCrawler()
    
    # 爬取详情
    content = await crawler.crawl_content_detail(content_id)
    
    if content:
        print("✅ 爬取成功\n")
        print(f"标题: {content['title']}")
        print(f"作者: {content['author_name']}")
        print(f"内容: {content['content'][:100]}...")
        print(f"点赞: {content['like_count']}")
        print(f"收藏: {content['collect_count']}")
        
        # 保存到数据库
        await job_pipeline.data_pipeline.process_content(content)
        print("\n✅ 已保存到数据库")
    else:
        print("❌ 爬取失败")
    
    # 关闭数据库
    await close_database()
    await close_mongodb()


async def crawl_user_example(user_id: str):
    """
    爬取用户信息示例
    
    Args:
        user_id: 用户ID
    """
    print(f"\n{'='*60}")
    print(f"爬取用户信息: {user_id}")
    print(f"{'='*60}\n")
    
    # 初始化数据库
    await init_database()
    
    # 初始化爬虫
    crawler = XiaohongshuCrawler()
    
    # 爬取用户信息
    user = await crawler.crawl_user_info(user_id)
    
    if user:
        print("✅ 爬取成功\n")
        print(f"用户名: {user['username']}")
        print(f"简介: {user['bio'][:100]}...")
        print(f"粉丝: {user['follower_count']}")
        print(f"关注: {user['following_count']}")
        print(f"笔记数: {user['note_count']}")
    else:
        print("❌ 爬取失败")
    
    # 关闭数据库
    await close_database()


async def batch_crawl_example():
    """
    批量爬取示例
    
    同时爬取多个关键词
    """
    keywords = ['美食', '旅行', '穿搭', '数码', '读书']
    
    print(f"\n{'='*60}")
    print(f"批量爬取示例")
    print(f"关键词: {', '.join(keywords)}")
    print(f"{'='*60}\n")
    
    # 初始化数据库
    await init_database()
    await init_mongodb()
    
    # 创建爬虫
    crawler = XiaohongshuCrawler()
    
    # 并发爬取（限制并发数）
    semaphore = asyncio.Semaphore(2)  # 最多2个并发
    
    async def crawl_with_limit(keyword):
        async with semaphore:
            print(f"\n🔍 开始爬取: {keyword}")
            contents = await crawler.crawl_by_keyword(keyword, limit=20)
            
            # 保存到数据库
            content_ids = await job_pipeline.data_pipeline.process_contents_batch(
                contents,
                save_raw=True
            )
            
            print(f"✅ {keyword}: 爬取 {len(contents)} 条，保存 {len(content_ids)} 条")
            return len(contents)
    
    # 执行批量爬取
    tasks = [crawl_with_limit(kw) for kw in keywords]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 显示结果
    total = sum(r for r in results if isinstance(r, int))
    print(f"\n{'='*60}")
    print(f"批量爬取完成，共爬取 {total} 条笔记")
    print(f"{'='*60}\n")
    
    # 显示总统计
    stats = crawler.get_stats()
    print(f"📊 总统计:")
    print(f"  - 总请求数: {stats['total_requests']}")
    print(f"  - 成功请求: {stats['success_requests']}")
    print(f"  - 成功率: {stats['success_rate']}%")
    
    # 关闭数据库
    await close_database()
    await close_mongodb()


async def main():
    """
    主函数
    """
    print("\n" + "="*60)
    print("社交内容创作平台 - 爬虫示例")
    print("="*60)
    
    # 检查环境变量
    if not os.getenv('DB_PASSWORD'):
        print("\n⚠️  警告: 未设置数据库密码")
        print("请在.env文件中配置DB_PASSWORD\n")
    
    # 选择示例
    print("\n请选择示例:")
    print("1. 关键词爬取")
    print("2. 笔记详情爬取")
    print("3. 用户信息爬取")
    print("4. 批量爬取")
    print("0. 退出")
    
    choice = input("\n请输入选项 (0-4): ").strip()
    
    if choice == '1':
        keyword = input("请输入关键词: ").strip()
        limit = input("请输入数量 (默认50): ").strip()
        limit = int(limit) if limit else 50
        
        await crawl_keyword_example(keyword, limit)
    
    elif choice == '2':
        content_id = input("请输入笔记ID: ").strip()
        await crawl_content_detail_example(content_id)
    
    elif choice == '3':
        user_id = input("请输入用户ID: ").strip()
        await crawl_user_example(user_id)
    
    elif choice == '4':
        confirm = input("确认执行批量爬取？(y/n): ").strip().lower()
        if confirm == 'y':
            await batch_crawl_example()
    
    else:
        print("退出程序")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
