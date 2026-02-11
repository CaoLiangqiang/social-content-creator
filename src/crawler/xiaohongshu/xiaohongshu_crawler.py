"""
小红书爬虫实现

基于BaseCrawler的小红书平台爬虫
"""

import asyncio
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..base.base_crawler import BaseCrawler, ParseError

logger = logging.getLogger(__name__)


class XiaohongshuCrawler(BaseCrawler):
    """
    小红书爬虫
    
    功能：
    - 关键词搜索笔记
    - 爬取笔记详情
    - 爬取用户信息
    - 爬取笔记评论
    """
    
    # 平台配置
    platform = 'xiaohongshu'
    base_url = 'https://www.xiaohongshu.com'
    
    # 小红书API端点
    api_base = 'https://edith.xiaohongshu.com/api'
    
    # 速率限制（更严格，小红书反爬较强）
    rate_limit = 5
    
    # 请求超时
    request_timeout = 15
    
    # User-Agent（使用移动端UA）
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.4720(0x28002d30) NetType/WIFI Language/zh_CN',
        'Mozilla/5.0 (Linux; Android 14; 23127PN0CC Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.43 Mobile Safari/537.36 XWEB/1200065 MMWEBSDK/20231202 MMWEBID/2307 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
        'Mozilla/5.0 (Linux; Android 13; 22081212C Build/TKQ1.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.43 Mobile Safari/537.36 XWEB/1200065 MMWEBSDK/20231202 MMWEBID/2307 MicroMessenger/8.0.47.2560(0x28002f33) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64',
    ]
    
    def __init__(self):
        super().__init__()
        self._cookie = None
        self._common_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.xiaohongshu.com/',
            'Origin': 'https://www.xiaohongshu.com',
        }
    
    def set_cookie(self, cookie: str):
        """
        设置Cookie（用于认证）
        
        Args:
            cookie: Cookie字符串
        """
        self._cookie = cookie
        self._common_headers['Cookie'] = cookie
        logger.info("Cookie set successfully")
    
    async def crawl_by_keyword(
        self,
        keyword: str,
        limit: int = 100,
        sort: str = 'general'  # general, time, popularity
    ) -> List[Dict]:
        """
        根据关键词搜索笔记
        
        Args:
            keyword: 搜索关键词
            limit: 最大爬取数量
            sort: 排序方式
            
        Returns:
            笔记列表
        """
        logger.info(f"[{self.platform}] Searching keyword: {keyword}")
        
        results = []
        page = 1
        
        while len(results) < limit:
            try:
                # 搜索API（实际端点需要根据抓包确定）
                url = f"{self.api_base}/sns/web/v1/search/notes"
                params = {
                    'keyword': keyword,
                    'page': page,
                    'page_size': min(20, limit - len(results)),
                    'sort': sort
                }
                
                response = await self._make_request(
                    url,
                    params=params,
                    headers=self._common_headers
                )
                
                if not response:
                    logger.warning(f"No response for keyword '{keyword}', page {page}")
                    break
                
                # 解析响应
                notes = self._parse_search_result(response)
                
                if not notes:
                    logger.info(f"No more notes found for keyword '{keyword}'")
                    break
                
                results.extend(notes)
                logger.info(f"Crawled {len(notes)} notes from page {page}")
                
                # 检查是否还有下一页
                if len(notes) < 20:
                    break
                
                page += 1
                
                # 延迟避免触发反爬
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error crawling keyword '{keyword}', page {page}: {str(e)}")
                break
        
        logger.info(
            f"[{self.platform}] Keyword search completed: "
            f"found {len(results)} notes for '{keyword}'"
        )
        
        return results[:limit]
    
    async def crawl_user_info(self, user_id: str) -> Optional[Dict]:
        """
        爬取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典
        """
        logger.info(f"[{self.platform}] Crawling user info: {user_id}")
        
        try:
            url = f"{self.api_base}/sns/web/v1/user/{user_id}/info"
            
            response = await self._make_request(
                url,
                headers=self._common_headers
            )
            
            if not response:
                logger.error(f"Failed to get user info for {user_id}")
                return None
            
            user_info = self._parse_user_info(response)
            
            if user_info and self.validate_data(user_info):
                logger.info(f"Successfully crawled user info: {user_id}")
                return user_info
            else:
                logger.warning(f"Invalid user info data for {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error crawling user info {user_id}: {str(e)}")
            return None
    
    async def crawl_content_detail(self, content_id: str) -> Optional[Dict]:
        """
        爬取笔记详情
        
        Args:
            content_id: 笔记ID
            
        Returns:
            笔记详情字典
        """
        logger.info(f"[{self.platform}] Crawling content detail: {content_id}")
        
        try:
            url = f"{self.api_base}/sns/web/v1/feed"
            params = {
                'source_note_id': content_id,
                'image_formats': 'jpg,webp,avif'
            }
            
            response = await self._make_request(
                url,
                params=params,
                headers=self._common_headers
            )
            
            if not response:
                logger.error(f"Failed to get content detail for {content_id}")
                return None
            
            content_detail = self._parse_content_detail(response)
            
            if content_detail and self.validate_data(content_detail):
                logger.info(f"Successfully crawled content detail: {content_id}")
                return content_detail
            else:
                logger.warning(f"Invalid content detail data for {content_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error crawling content detail {content_id}: {str(e)}")
            return None
    
    async def crawl_comments(
        self,
        content_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        爬取笔记评论
        
        Args:
            content_id: 笔记ID
            limit: 最大评论数量
            
        Returns:
            评论列表
        """
        logger.info(f"[{self.platform}] Crawling comments for: {content_id}")
        
        results = []
        cursor = ''
        
        while len(results) < limit:
            try:
                url = f"{self.api_base}/sns/web/v2/comment/page"
                params = {
                    'note_id': content_id,
                    'cursor': cursor,
                    'top_comment_id': '',
                    'image_formats': 'jpg,webp,avif'
                }
                
                response = await self._make_request(
                    url,
                    params=params,
                    headers=self._common_headers
                )
                
                if not response:
                    logger.warning(f"No response for comments of {content_id}")
                    break
                
                # 解析评论
                comments = self._parse_comments(response)
                
                if not comments:
                    logger.info(f"No more comments for {content_id}")
                    break
                
                results.extend(comments)
                logger.info(f"Crawled {len(comments)} comments (total: {len(results)})")
                
                # 获取下一页游标
                cursor = self._extract_cursor(response)
                if not cursor:
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error crawling comments for {content_id}: {str(e)}")
                break
        
        logger.info(
            f"[{self.platform}] Comment crawling completed: "
            f"{len(results)} comments for {content_id}"
        )
        
        return results[:limit]
    
    def _parse_search_result(self, response: dict) -> List[Dict]:
        """
        解析搜索结果
        
        Args:
            response: API响应
            
        Returns:
            笔记列表
        """
        try:
            # 实际解析逻辑需要根据API响应结构确定
            # 这里提供一个示例结构
            items = response.get('data', {}).get('items', [])
            
            notes = []
            for item in items:
                note_data = item.get('model', {}).get('note_card', {})
                
                note = {
                    'platform_content_id': note_data.get('id', ''),
                    'title': note_data.get('display_title', ''),
                    'content': note_data.get('desc', ''),
                    'author_id': note_data.get('user', {}).get('user_id', ''),
                    'author_name': note_data.get('user', {}).get('nick_name', ''),
                    'author_avatar': note_data.get('user', {}).get('avatar', ''),
                    'cover_url': note_data.get('cover', {}).get('url_default', ''),
                    'like_count': note_data.get('interact_info', {}).get('liked_count', 0),
                    'view_count': note_data.get('interact_info', {}).get('view_count', 0),
                    'collect_count': note_data.get('interact_info', {}).get('collected_count', 0),
                    'comment_count': note_data.get('interact_info', {}).get('comment_count', 0),
                    'url': f"{self.base_url}/explore/{note_data.get('id', '')}",
                    'crawled_at': datetime.now().isoformat()
                }
                
                # 提取标签
                tags = []
                for tag in note_data.get('topic_list', []):
                    tags.append(tag.get('name', ''))
                note['tags'] = tags
                
                notes.append(note)
            
            return notes
            
        except Exception as e:
            logger.error(f"Error parsing search result: {str(e)}")
            raise ParseError(f"Failed to parse search result: {str(e)}")
    
    def _parse_user_info(self, response: dict) -> Optional[Dict]:
        """
        解析用户信息
        
        Args:
            response: API响应
            
        Returns:
            用户信息字典
        """
        try:
            user_data = response.get('data', {}).get('user', {})
            
            user = {
                'platform_user_id': user_data.get('user_id', ''),
                'username': user_data.get('nick_name', ''),
                'avatar_url': user_data.get('avatar', ''),
                'bio': user_data.get('desc', ''),
                'gender': user_data.get('gender', 0),  # 0: 未知, 1: 男, 2: 女
                'follower_count': user_data.get('follows', 0),
                'following_count': user_data.get('fans', 0),
                'note_count': user_data.get('note_count', 0),
                'ip_location': user_data.get('ip_location', ''),
                'crawled_at': datetime.now().isoformat()
            }
            
            return user
            
        except Exception as e:
            logger.error(f"Error parsing user info: {str(e)}")
            raise ParseError(f"Failed to parse user info: {str(e)}")
    
    def _parse_content_detail(self, response: dict) -> Optional[Dict]:
        """
        解析笔记详情
        
        Args:
            response: API响应
            
        Returns:
            笔记详情字典
        """
        try:
            note_data = response.get('data', {}).get('items', [{}])[0].get('note_card', {})
            
            # 提取图片
            images = []
            for image in note_data.get('image_list', []):
                images.append(image.get('url_default', ''))
            
            # 提取话题
            topics = []
            for topic in note_data.get('topic_list', []):
                topics.append(topic.get('name', ''))
            
            content = {
                'platform_content_id': note_data.get('id', ''),
                'title': note_data.get('display_title', ''),
                'content': note_data.get('desc', ''),
                'content_type': 'note',
                'author_id': note_data.get('user', {}).get('user_id', ''),
                'author_name': note_data.get('user', {}).get('nick_name', ''),
                'author_avatar': note_data.get('user', {}).get('avatar', ''),
                'images': images,
                'video_url': note_data.get('video', {}).get('media', {}).get('stream', {}).get('h264', [{}])[0].get('master_url', ''),
                'like_count': note_data.get('interact_info', {}).get('liked_count', 0),
                'collect_count': note_data.get('interact_info', {}).get('collected_count', 0),
                'comment_count': note_data.get('interact_info', {}).get('comment_count', 0),
                'share_count': note_data.get('interact_info', {}).get('share_count', 0),
                'published_at': datetime.fromtimestamp(
                    note_data.get('time', 0) / 1000
                ).isoformat() if note_data.get('time') else None,
                'url': f"{self.base_url}/explore/{note_data.get('id', '')}",
                'tags': note_data.get('tag_list', []),
                'topics': topics,
                'crawled_at': datetime.now().isoformat()
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error parsing content detail: {str(e)}")
            raise ParseError(f"Failed to parse content detail: {str(e)}")
    
    def _parse_comments(self, response: dict) -> List[Dict]:
        """
        解析评论列表
        
        Args:
            response: API响应
            
        Returns:
            评论列表
        """
        try:
            comments_data = response.get('data', {}).get('comments', [])
            
            comments = []
            for comment_data in comments_data:
                comment = {
                    'platform_comment_id': comment_data.get('id', ''),
                    'content': comment_data.get('content', ''),
                    'user_id': comment_data.get('user_info', {}).get('user_id', ''),
                    'username': comment_data.get('user_info', {}).get('nick_name', ''),
                    'like_count': comment_data.get('like_count', 0),
                    'parent_comment_id': comment_data.get('parent_comment', {}).get('id', ''),
                    'created_at': datetime.fromtimestamp(
                        comment_data.get('create_time', 0) / 1000
                    ).isoformat() if comment_data.get('create_time') else None,
                    'ip_location': comment_data.get('ip_location', '')
                }
                
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Error parsing comments: {str(e)}")
            raise ParseError(f"Failed to parse comments: {str(e)}")
    
    def _extract_cursor(self, response: dict) -> str:
        """
        从响应中提取下一页游标
        
        Args:
            response: API响应
            
        Returns:
            游标字符串
        """
        try:
            return response.get('data', {}).get('cursor', '')
        except:
            return ''
