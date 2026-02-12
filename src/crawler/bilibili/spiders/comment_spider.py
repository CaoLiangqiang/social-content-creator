"""
B站评论爬虫

基于BaseCrawler的B站评论数据爬虫
"""

import asyncio
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ...base.base_crawler import BaseCrawler, ParseError

logger = logging.getLogger(__name__)


class BilibiliCommentSpider(BaseCrawler):
    name = 'bilibili_comment'  # Scrapy要求的name属性
    """
    B站评论数据爬虫
    
    功能：
    - 爬取B站视频评论
    - 支持分页评论
    - 解析评论树形结构
    - 爬取回复评论
    """
    
    # 平台配置
    platform = 'bilibili'
    base_url = 'https://www.bilibili.com'
    
    # B站评论API端点
    comment_api_base = 'https://api.bilibili.com'
    
    # 速率限制（评论API限制较严格）
    rate_limit = 2
    
    # 请求超时
    request_timeout = 10
    
    # User-Agent
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 14; SM-G991B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.230 Mobile Safari/537.36 XWEB/1160000 MMWEBSDK/20231202 MMWEBID/3403 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
    ]
    
    # 常用的请求头
    common_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
    }
    
    def __init__(self):
        super().__init__()
        self._common_headers = {
            **self.common_headers,
            'User-Agent': self.user_agents[0],
        }
    
    async def crawl_comments_by_aid(
        self,
        aid: str,
        limit: int = 100,
        page: int = 1
    ) -> List[Dict]:
        """
        通过AV号爬取评论
        
        Args:
            aid: 视频AV号
            limit: 最大评论数量
            page: 起始页码
            
        Returns:
            评论列表
        """
        logger.info(f"[{self.platform}] Crawling comments by aid: {aid}")
        
        try:
            # 获取视频评论总数
            total_comments = await self._get_comment_count(aid)
            if total_comments is None:
                logger.error(f"Failed to get comment count for aid: {aid}")
                return []
            
            # 计算需要爬取的页数
            total_pages = min((total_comments + 49) // 50, 10)  # B站最多支持10页评论
            
            all_comments = []
            current_page = page
            
            while len(all_comments) < limit and current_page <= total_pages:
                try:
                    # 获取评论
                    comments = await self._get_page_comments(aid, current_page)
                    
                    if not comments:
                        logger.warning(f"No comments found for aid: {aid}, page: {current_page}")
                        break
                    
                    all_comments.extend(comments)
                    logger.info(f"Crawled {len(comments)} comments from page {current_page} (total: {len(all_comments)})")
                    
                    current_page += 1
                    
                    # 延迟避免触发反爬
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error crawling comments for aid {aid}, page {current_page}: {str(e)}")
                    break
            
            logger.info(f"Comment crawling completed: {len(all_comments)} comments for aid: {aid}")
            return all_comments[:limit]
            
        except Exception as e:
            logger.error(f"Error crawling comments for aid {aid}: {str(e)}")
            return []
    
    async def crawl_comments_by_bvid(
        self,
        bvid: str,
        limit: int = 100,
        page: int = 1
    ) -> List[Dict]:
        """
        通过BV号爬取评论
        
        Args:
            bvid: 视频BV号
            limit: 最大评论数量
            page: 起始页码
            
        Returns:
            评论列表
        """
        logger.info(f"[{self.platform}] Crawling comments by bvid: {bvid}")
        
        try:
            # 通过BV号获取AV号
            aid = await self._get_aid_by_bvid(bvid)
            if not aid:
                logger.error(f"Failed to get aid for bvid: {bvid}")
                return []
            
            return await self.crawl_comments_by_aid(aid, limit, page)
            
        except Exception as e:
            logger.error(f"Error crawling comments for bvid {bvid}: {str(e)}")
            return []
    
    async def crawl_comment_replies(
        self,
        aid: str,
        parent_rpid: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        爬取评论的回复
        
        Args:
            aid: 视频AV号
            parent_rpid: 父评论ID
            limit: 最大回复数量
            
        Returns:
            回复列表
        """
        logger.info(f"[{self.platform}] Crawling comment replies for aid: {aid}, parent_rpid: {parent_rpid}")
        
        try:
            api_url = f"{self.comment_api_base}/x/v2/reply"
            
            replies = []
            offset = 0
            
            while len(replies) < limit:
                params = {
                    'type': 1,
                    'oid': aid,
                    'root': parent_rpid,
                    'ps': 10,
                    'next': offset
                }
                
                response = await self._make_api_request(api_url, params)
                
                if not response:
                    break
                
                page_replies = self._parse_comment_replies(response, aid, parent_rpid)
                
                if not page_replies:
                    break
                
                replies.extend(page_replies)
                logger.info(f"Crawled {len(page_replies)} replies (total: {len(replies)})")
                
                offset += 10
                
                # 延迟
                await asyncio.sleep(1)
            
            logger.info(f"Reply crawling completed: {len(replies)} replies for aid: {aid}")
            return replies[:limit]
            
        except Exception as e:
            logger.error(f"Error crawling comment replies for aid {aid}: {str(e)}")
            return []
    
    async def crawl_hot_comments(
        self,
        aid: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        爬取热评
        
        Args:
            aid: 视频AV号
            limit: 最大热评数量
            
        Returns:
            热评列表
        """
        logger.info(f"[{self.platform}] Crawling hot comments for aid: {aid}")
        
        try:
            api_url = f"{self.comment_api_base}/x/v2/reply/hot"
            
            params = {
                'oid': aid,
                'ps': limit,
                'type': 1
            }
            
            response = await self._make_api_request(api_url, params)
            
            if not response:
                logger.error(f"Failed to get hot comments for aid: {aid}")
                return []
            
            hot_comments = self._parse_hot_comments(response, aid)
            
            logger.info(f"Crawled {len(hot_comments)} hot comments for aid: {aid}")
            return hot_comments[:limit]
            
        except Exception as e:
            logger.error(f"Error crawling hot comments for aid {aid}: {str(e)}")
            return []
    
    async def _get_comment_count(self, aid: str) -> Optional[int]:
        """
        获取评论总数
        
        Args:
            aid: 视频AV号
            
        Returns:
            评论总数
        """
        try:
            api_url = f"{self.comment_api_base}/x/v2/reply"
            params = {
                'type': 1,
                'oid': aid,
                'ps': 1
            }
            
            response = await self._make_api_request(api_url, params)
            
            if response:
                return response.get('page', {}).get('count', 0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting comment count for aid {aid}: {str(e)}")
            return None
    
    async def _get_page_comments(self, aid: str, page: int) -> List[Dict]:
        """
        获取指定页的评论
        
        Args:
            aid: 视频AV号
            page: 页码
            
        Returns:
            评论列表
        """
        try:
            api_url = f"{self.comment_api_base}/x/v2/reply"
            
            params = {
                'type': 1,
                'oid': aid,
                'ps': 50,
                'pn': page
            }
            
            response = await self._make_api_request(api_url, params)
            
            if response:
                return self._parse_comments(response, aid)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting page comments for aid {aid}: {str(e)}")
            return []
    
    async def _get_aid_by_bvid(self, bvid: str) -> Optional[str]:
        """
        通过BV号获取AV号
        
        Args:
            bvid: 视频BV号
            
        Returns:
            视频AV号
        """
        try:
            api_url = f"{self.comment_api_base}/x/web-interface/view"
            params = {'bvid': bvid}
            
            response = await self._make_api_request(api_url, params)
            
            if response:
                return response.get('aid')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting aid by bvid {bvid}: {str(e)}")
            return None
    
    async def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        发起API请求
        
        Args:
            url: API URL
            params: 请求参数
            
        Returns:
            API响应数据
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(
                headers=self._common_headers,
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    else:
                        logger.warning(f"API request failed: {response.status}")
                        return None
                        
        except ImportError:
            # 如果没有aiohttp，使用同步请求
            import requests
            
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self._common_headers,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('data', {})
                else:
                    logger.warning(f"API request failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                return None
    
    def _parse_comments(self, data: Dict, aid: str) -> List[Dict]:
        """
        解析评论数据
        
        Args:
            data: API响应数据
            aid: 视频AV号
            
        Returns:
            评论列表
        """
        try:
            replies = data.get('replies', [])
            comments = []
            
            for reply in replies:
                comment = {
                    'comment_id': str(reply.get('rpid', '')),
                    'content': reply.get('content', {}).get('message', ''),
                    'author': reply.get('member', {}).get('uname', ''),
                    'author_id': reply.get('mid', ''),
                    'likes': reply.get('like', 0),
                    'ctime': datetime.fromtimestamp(reply.get('ctime', 0)).isoformat() if reply.get('ctime') else None,
                    'rpid': str(reply.get('rpid', '')),
                    'parent': str(reply.get('parent', '')),
                    'root': str(reply.get('root', '')),
                    'mid': reply.get('mid', ''),
                    'location': reply.get('location', ''),
                    'message': reply.get('content', {}).get('message', ''),
                    'plat': reply.get('plat', ''),
                    'type': reply.get('type', 1),
                    'oid': aid,
                    'type_id': 1,
                    'rcount': reply.get('rcount', 0),
                    'state': reply.get('state', 0),
                    'mid_hash': reply.get('mid_hash', ''),
                    'video_id': aid,
                    'crawl_time': datetime.now().isoformat()
                }
                
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error parsing comments: {str(e)}")
            return []
    
    def _parse_comment_replies(self, data: Dict, aid: str, parent_rpid: str) -> List[Dict]:
        """
        解析评论回复
        
        Args:
            data: API响应数据
            aid: 视频AV号
            parent_rpid: 父评论ID
            
        Returns:
            回复列表
        """
        try:
            replies = data.get('replies', [])
            comment_replies = []
            
            for reply in replies:
                comment_reply = {
                    'comment_id': str(reply.get('rpid', '')),
                    'content': reply.get('content', {}).get('message', ''),
                    'author': reply.get('member', {}).get('uname', ''),
                    'author_id': reply.get('mid', ''),
                    'likes': reply.get('like', 0),
                    'ctime': datetime.fromtimestamp(reply.get('ctime', 0)).isoformat() if reply.get('ctime') else None,
                    'rpid': str(reply.get('rpid', '')),
                    'parent': parent_rpid,
                    'root': parent_rpid,  # 回复的root与parent相同
                    'mid': reply.get('mid', ''),
                    'location': reply.get('location', ''),
                    'message': reply.get('content', {}).get('message', ''),
                    'plat': reply.get('plat', ''),
                    'type': reply.get('type', 1),
                    'oid': aid,
                    'type_id': 1,
                    'rcount': reply.get('rcount', 0),
                    'state': reply.get('state', 0),
                    'mid_hash': reply.get('mid_hash', ''),
                    'video_id': aid,
                    'crawl_time': datetime.now().isoformat()
                }
                
                comment_replies.append(comment_reply)
            
            return comment_replies
            
        except Exception as e:
            logger.error(f"Error parsing comment replies: {str(e)}")
            return []
    
    def _parse_hot_comments(self, data: Dict, aid: str) -> List[Dict]:
        """
        解析热评数据
        
        Args:
            data: API响应数据
            aid: 视频AV号
            
        Returns:
            热评列表
        """
        try:
            replies = data.get('hots', [])
            hot_comments = []
            
            for reply in replies:
                hot_comment = {
                    'comment_id': str(reply.get('rpid', '')),
                    'content': reply.get('content', {}).get('message', ''),
                    'author': reply.get('member', {}).get('uname', ''),
                    'author_id': reply.get('mid', ''),
                    'likes': reply.get('like', 0),
                    'ctime': datetime.fromtimestamp(reply.get('ctime', 0)).isoformat() if reply.get('ctime') else None,
                    'rpid': str(reply.get('rpid', '')),
                    'parent': str(reply.get('parent', '')),
                    'root': str(reply.get('root', '')),
                    'mid': reply.get('mid', ''),
                    'location': reply.get('location', ''),
                    'message': reply.get('content', {}).get('message', ''),
                    'plat': reply.get('plat', ''),
                    'type': reply.get('type', 1),
                    'oid': aid,
                    'type_id': 1,
                    'rcount': reply.get('rcount', 0),
                    'state': reply.get('state', 0),
                    'mid_hash': reply.get('mid_hash', ''),
                    'video_id': aid,
                    'crawl_time': datetime.now().isoformat()
                }
                
                hot_comments.append(hot_comment)
            
            return hot_comments
            
        except Exception as e:
            logger.error(f"Error parsing hot comments: {str(e)}")
            return []
    
    def build_comment_tree(self, comments: List[Dict]) -> Dict:
        """
        构建评论树形结构
        
        Args:
            comments: 评论列表
            
        Returns:
            评论树形结构
        """
        comment_tree = {}
        
        # 第一遍：构建基本节点
        for comment in comments:
            rpid = comment.get('rpid', '')
            parent = comment.get('parent', '')
            
            if rpid not in comment_tree:
                comment_tree[rpid] = {
                    'comment': comment,
                    'replies': []
                }
        
        # 第二遍：构建父子关系
        for comment in comments:
            rpid = comment.get('rpid', '')
            parent = comment.get('parent', '')
            
            if parent and parent != '0' and parent in comment_tree:
                comment_tree[parent]['replies'].append(comment_tree[rpid])
        
        return comment_tree
    
    def get_comment_stats(self, comments: List[Dict]) -> Dict:
        """
        获取评论统计信息
        
        Args:
            comments: 评论列表
            
        Returns:
            统计信息字典
        """
        if not comments:
            return {}
        
        stats = {
            'total_count': len(comments),
            'total_likes': sum(comment.get('likes', 0) for comment in comments),
            'average_likes': 0,
            'author_counts': {},
            'time_distribution': {'morning': 0, 'afternoon': 0, 'evening': 0, 'night': 0}
        }
        
        # 计算平均点赞数
        stats['average_likes'] = stats['total_likes'] / stats['total_count']
        
        # 统计作者数量
        for comment in comments:
            author = comment.get('author', 'Unknown')
            stats['author_counts'][author] = stats['author_counts'].get(author, 0) + 1
        
        # 统计时间分布
        for comment in comments:
            ctime = comment.get('ctime')
            if ctime:
                try:
                    # 解析时间并分类
                    time_obj = datetime.fromisoformat(ctime.replace('Z', '+00:00'))
                    hour = time_obj.hour
                    
                    if 6 <= hour < 12:
                        stats['time_distribution']['morning'] += 1
                    elif 12 <= hour < 18:
                        stats['time_distribution']['afternoon'] += 1
                    elif 18 <= hour < 24:
                        stats['time_distribution']['evening'] += 1
                    else:
                        stats['time_distribution']['night'] += 1
                        
                except Exception:
                    continue
        
        return stats