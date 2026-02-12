#!/usr/bin/env python3
"""
抖音爬虫实现（基于requests）

> 🎵 抖音爬虫完整实现
> 开发者: 智宝 (AI助手)
"""

import asyncio
import sys
import re
import json
import requests
from pathlib import Path
from typing import Dict, Optional, List
from bs4 import BeautifulSoup


# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.douyin.items import DouyinVideoItem


class DouyinVideoCrawler:
    """抖音视频爬虫（基于requests）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.douyin.com/',
        })
        
        self.stats = {
            'success': 0,
            'failed': 0,
            'total': 0
        }
    
    def crawl_video_by_url(self, url: str) -> Optional[DouyinVideoItem]:
        """
        爬取抖音视频
        
        Args:
            url: 视频URL
            
        Returns:
            DouyinVideoItem对象
        """
        self.stats['total'] += 1
        
        try:
            # 发送请求
            print(f"访问URL: {url}")
            response = self.session.get(url, allow_redirects=True, timeout=15)
            
            print(f"状态码: {response.status_code}")
            print(f"最终URL: {response.url}")
            
            if response.status_code != 200:
                print(f"❌ HTTP状态码异常: {response.status_code}")
                self.stats['failed'] += 1
                return None
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取script标签中的数据
            scripts = soup.find_all('script')
            print(f"找到 {len(scripts)} 个script标签")
            
            # 查找包含视频数据的script
            for i, script in enumerate(scripts):
                script_text = script.string or ''
                
                # 查找特定标识
                if 'window.__INITIAL_STATE__' in script_text or 'videoData' in script_text:
                    print(f"\\nScript #{i} 包含视频数据")
                    
                    # 尝试提取JSON
                    video_data = self._extract_video_data(script_text)
                    
                    if video_data:
                        self.stats['success'] += 1
                        return video_data
            
            # 如果没找到，尝试其他方法
            print("\\n尝试从HTML直接提取...")
            return self._extract_from_html(soup)
            
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            self.stats['failed'] += 1
            return None
    
    def _extract_video_data(self, script_text: str) -> Optional[DouyinVideoItem]:
        """从script文本中提取视频数据"""
        
        # 方法1: 提取__INITIAL_STATE__
        initial_state_match = re.search(r'window\\.__INITIAL_STATE__\\s*=\\s*(\\{.*?\\});', script_text)
        
        if initial_state_match:
            try:
                print("找到__INITIAL_STATE__")
                data = json.loads(initial_state_match.group(1))
                
                # 从数据中提取视频信息
                return self._parse_video_from_state(data)
            except:
                pass
        
        # 方法2: 查找videoData
        video_match = re.search(r'videoData["\']?\\s*=\\s*(\\{.*?\\});', script_text)
        
        if video_match:
            try:
                print("找到videoData")
                data = json.loads(video_match.group(1))
                return self._parse_video_from_data(data)
            except:
                pass
        
        # 方法3: 查找awemeId
        aweme_match = re.search(r'"aweme_id":"?(\\d+)"?', script_text)
        if aweme_match:
            print(f"找到aweme_id: {aweme_match.group(1)}")
            # 可以用aweme_id构造API请求
        
        return None
    
    def _parse_video_from_state(self, data: Dict) -> Optional[DouyinVideoItem]:
        """从INITIAL_STATE解析视频数据"""
        try:
            # 尝试不同的数据路径
            video_info = None
            
            # 路径1: data.videoInfo
            if 'videoInfo' in data:
                video_info = data['videoInfo']
                print("从videoInfo提取")
            
            # 路径2: data.aweme
            elif 'aweme' in data:
                video_info = data['aweme']
                print("从aweme提取")
            
            # 路径3: data.awemeDetail
            elif 'awemeDetail' in data:
                video_info = data['awemeDetail']
                print("从awemeDetail提取")
            
            if not video_info:
                print("⚠️ 未找到视频数据")
                return None
            
            print(f"视频数据键: {list(video_info.keys())}")
            return self._create_video_item(video_info)
            
        except Exception as e:
            print(f"解析INITIAL_STATE失败: {e}")
            return None
    
    def _parse_video_from_data(self, data: Dict) -> Optional[DouyinVideoItem]:
        """从videoData解析"""
        try:
            return self._create_video_item(data)
        except Exception as e:
            print(f"解析videoData失败: {e}")
            return None
    
    def _create_video_item(self, data: Dict) -> DouyinVideoItem:
        """创建视频对象"""
        
        video = DouyinVideoItem()
        
        # 提取基础字段
        video.video_id = str(data.get('aweme_id') or data.get('awemeId', ''))
        video.title = data.get('desc', '')
        video.desc = data.get('desc', '')
        
        # 统计数据
        stats = data.get('statistics', {})
        from src.crawler.douyin.items import DouyinStatistics
        video.statistics = DouyinStatistics(
            digg_count=stats.get('digg_count', 0),
            comment_count=stats.get('comment_count', 0),
            share_count=stats.get('share_count', 0),
            play_count=stats.get('play_count', 0),
            collect_count=stats.get('collect_count', 0)
        )
        
        # 作者信息
        author_data = data.get('author', {})
        from src.crawler.douyin.items import DouyinAuthor
        video.author = DouyinAuthor(
            uid=str(author_data.get('uid', '')),
            nickname=author_data.get('nickname', ''),
            avatar_thumb=author_data.get('avatar_thumb', {}).get('url_list', [''])[0],
            signature=author_data.get('signature', ''),
            follower_count=author_data.get('follower_count', 0),
            following_count=author_data.get('following_count', 0),
            aweme_count=author_data.get('aweme_count', 0)
        )
        
        # 视频信息
        video_data = data.get('video', {})
        from src.crawler.douyin.items import DouyinVideoInfo
        video.video = DouyinVideoInfo(
            play_addr=video_data.get('play_addr', {}).get('url_list', [''])[0],
            cover=video_data.get('cover', {}).get('url_list', [''])[0],
            duration=video_data.get('duration', 0),
            width=video_data.get('width', 0),
            height=video_data.get('height', 0)
        )
        
        return video
    
    def _extract_from_html(self, soup: BeautifulSoup) -> Optional[DouyinVideoItem]:
        """从HTML直接提取"""
        # 查找标题
        title_elem = soup.find('meta', property='og:title')
        title = title_elem.get('content', '') if title_elem else ''
        
        # 查找描述
        desc_elem = soup.find('meta', property='og:description')
        desc = desc_elem.get('content', '') if desc_elem else ''
        
        # 查找视频URL
        video_elem = soup.find('meta', property='og:video')
        video_url = video_elem.get('content', '') if video_elem else ''
        
        if title or desc:
            print(f"\\n从HTML提取:")
            print(f"  标题: {title}")
            print(f"  描述: {desc[:100]}")
            print(f"  视频: {video_url[:100]}")
        
        return None


async def main():
    """测试爬虫"""
    print("""
╔══════════════════════════════════════════════════════════╗
║       🎵 抖音爬虫实现测试 - 智宝出品 🌸              ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    url = "https://v.douyin.com/arLquTQPBYM/"
    print(f"测试URL: {url}\\n")
    
    crawler = DouyinVideoCrawler()
    video = crawler.crawl_video_by_url(url)
    
    if video:
        print("\\n" + "="*60)
        print("✅ 视频爬取成功！")
        print("="*60)
        print(f"视频ID: {video.video_id}")
        print(f"标题: {video.title}")
        print(f"点赞数: {video.statistics.digg_count}")
        print(f"评论数: {video.statistics.comment_count}")
        print(f"创作者: {video.author.nickname}")
    else:
        print("\\n⚠️ 视频爬取失败，需要进一步完善数据提取逻辑")
    
    print(f"\\n统计: {crawler.stats}")


if __name__ == "__main__":
    asyncio.run(main())
