#!/usr/bin/env python3
"""
爬虫命令行入口

支持通过命令行参数调用各平台爬虫，输出JSON结果
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler
from src.crawler.douyin.douyin_crawler_enhanced import DouyinCrawlerEnhanced


async def crawl_bilibili(args):
    """B站爬虫"""
    crawler = BilibiliCrawler()
    
    if args.type == 'video':
        if args.bvid:
            result = await crawler.crawl_video_full(args.bvid)
        elif args.url:
            import re
            bvid_match = re.search(r'BV[a-zA-Z0-9]+', args.url)
            if bvid_match:
                result = await crawler.crawl_video_full(bvid_match.group())
            else:
                result = {'error': 'Invalid Bilibili URL, cannot extract BV ID'}
        else:
            result = {'error': 'Please provide --bvid or --url'}
            
    elif args.type == 'user':
        if args.mid:
            result = await crawler.crawl_user(args.mid)
        elif args.url:
            import re
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                if 'b23.tv' in args.url:
                    async with session.get(args.url, allow_redirects=True) as response:
                        args.url = str(response.url)
                
                mid_match = re.search(r'/(\d+)', args.url)
                if mid_match:
                    result = await crawler.crawl_user(mid_match.group(1))
                else:
                    result = {'error': 'Invalid Bilibili user URL'}
        else:
            result = {'error': 'Please provide --mid or --url'}
            
    elif args.type == 'search':
        if args.keyword:
            results = await crawler.crawl_videos_by_keyword(args.keyword, limit=args.limit or 20)
            result = {'videos': results, 'count': len(results)}
        else:
            result = {'error': 'Please provide --keyword for search'}
    else:
        result = {'error': f'Unknown type: {args.type}'}
    
    return result


async def crawl_douyin(args):
    """抖音爬虫（增强版）"""
    crawler = DouyinCrawlerEnhanced()
    
    try:
        if args.type == 'video':
            if args.url:
                result = await crawler.crawl_by_url(args.url)
            elif args.video_id:
                result = await crawler.crawl_video(args.video_id)
            else:
                result = {'error': 'Please provide --url or --video-id'}
                
        elif args.type == 'user':
            if args.user_id:
                result = await crawler.crawl_user(args.user_id)
            elif args.url:
                result = await crawler.crawl_by_url(args.url)
            else:
                result = {'error': 'Please provide --user-id or --url'}
                
        elif args.type == 'comments':
            if args.video_id:
                comments = await crawler.crawl_comments(args.video_id, limit=args.limit or 100)
                result = {'video_id': args.video_id, 'comments': comments, 'count': len(comments)}
            else:
                result = {'error': 'Please provide --video-id for comments'}
                
        elif args.type == 'user-videos':
            if args.user_id:
                videos = await crawler.crawl_user_videos(args.user_id, limit=args.limit or 50)
                result = {'user_id': args.user_id, 'videos': videos, 'count': len(videos)}
            else:
                result = {'error': 'Please provide --user-id for user videos'}
        else:
            result = {'error': f'Unknown type: {args.type}'}
        
        result['stats'] = crawler.get_stats()
        return result
        
    finally:
        await crawler.close()


async def crawl_xiaohongshu(args):
    """小红书爬虫"""
    try:
        from src.crawler.xiaohongshu.xiaohongshu_crawler import XiaohongshuCrawler
        crawler = XiaohongshuCrawler()
        
        try:
            if args.type == 'note' and args.note_id:
                result = await crawler.crawl_note(args.note_id)
            elif args.type == 'user' and args.user_id:
                result = await crawler.crawl_user(args.user_id)
            elif args.type == 'search' and args.keyword:
                notes = await crawler.crawl_by_keyword(args.keyword, limit=args.limit or 20)
                result = {'keyword': args.keyword, 'notes': notes, 'count': len(notes)}
            elif args.type == 'comments' and args.note_id:
                comments = await crawler.crawl_comments(args.note_id, limit=args.limit or 100)
                result = {'note_id': args.note_id, 'comments': comments, 'count': len(comments)}
            elif args.url:
                result = await crawler.crawl_by_url(args.url)
            else:
                result = {'error': 'Please provide --note-id, --user-id, --keyword or --url'}
            
            return result
        finally:
            await crawler.close()
            
    except ImportError as e:
        return {'error': f'Xiaohongshu crawler not available: {str(e)}'}


async def auto_detect(args):
    """自动检测平台并爬取"""
    url = args.url
    
    if 'bilibili.com' in url or 'b23.tv' in url:
        args.type = 'video'
        return await crawl_bilibili(args)
    elif 'douyin.com' in url or 'v.douyin.com' in url:
        args.type = 'video'
        return await crawl_douyin(args)
    elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
        args.type = 'note'
        return await crawl_xiaohongshu(args)
    else:
        return {'error': 'Unsupported platform'}


def main():
    parser = argparse.ArgumentParser(description='Social Media Crawler CLI')
    parser.add_argument('--platform', '-p', choices=['bilibili', 'douyin', 'xiaohongshu', 'auto'],
                        default='auto', help='Target platform')
    parser.add_argument('--type', '-t', choices=['video', 'user', 'note', 'search', 'comments', 'user-videos'],
                        default='video', help='Content type to crawl')
    parser.add_argument('--url', '-u', help='Content URL')
    parser.add_argument('--bvid', '-b', help='Bilibili BV ID')
    parser.add_argument('--mid', '-m', help='Bilibili user MID')
    parser.add_argument('--video-id', help='Douyin video ID')
    parser.add_argument('--user-id', help='User ID (Douyin/Xiaohongshu)')
    parser.add_argument('--note-id', '-n', help='Xiaohongshu note ID')
    parser.add_argument('--keyword', '-k', help='Search keyword')
    parser.add_argument('--limit', '-l', type=int, default=20, help='Result limit')
    
    args = parser.parse_args()
    
    try:
        if args.platform == 'auto' and args.url:
            result = asyncio.run(auto_detect(args))
        elif args.platform == 'bilibili':
            result = asyncio.run(crawl_bilibili(args))
        elif args.platform == 'douyin':
            result = asyncio.run(crawl_douyin(args))
        elif args.platform == 'xiaohongshu':
            result = asyncio.run(crawl_xiaohongshu(args))
        else:
            result = {'error': 'Please specify --platform and required parameters'}
        
        print(json.dumps(result, ensure_ascii=False, default=str))
        
    except Exception as e:
        error_result = {'error': str(e)}
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
