import scrapy
import re
import json
from datetime import datetime
from urllib.parse import urljoin

from ..base.base_crawler import BaseCrawler
from ..utils.logger import logger
from ..items import XiaohongshuUserItem

class XiaohongshuUserSpider(BaseCrawler):
    """小红书用户爬虫"""
    
    name = "xiaohongshu_user"
    platform = "xiaohongshu"
    
    # 用户URL模式
    user_url_patterns = [
        r'https://www\.xiaohongshu\.com/user/profile/[a-zA-Z0-9]+',
        r'https://www\.xiaohongshu\.com/user/[a-zA-Z0-9]+',
    ]
    
    def __init__(self, start_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 设置起始URL
        if start_urls:
            if isinstance(start_urls, str):
                self.start_urls = [start_urls]
            else:
                self.start_urls = start_urls
        else:
            # 默认从热门用户开始
            self.start_urls = [
                'https://www.xiaohongshu.com/user/profile',
                'https://www.xiaohongshu.com/discovery',
            ]
        
        logger.info(f"用户爬虫初始化完成，起始URL: {self.start_urls}")
    
    def start_requests(self):
        """开始请求"""
        for url in self.start_urls:
            yield self._make_request(url, callback=self.parse_main_page)
    
    def parse_main_page(self, response):
        """解析主页面，提取用户链接"""
        logger.info(f"解析主页面: {response.url}")
        
        # 提取用户链接
        user_links = self._extract_user_links(response)
        
        for link in user_links:
            yield self._make_request(link, callback=self.parse_user_detail)
    
    def parse_user_detail(self, response):
        """解析用户详情"""
        logger.info(f"解析用户详情: {response.url}")
        
        try:
            # 创建用户item
            item = XiaohongshuUserItem()
            
            # 提取基本信息
            item['url'] = response.url
            item['user_id'] = self._extract_user_id(response.url)
            item['username'] = self._extract_username(response)
            item['bio'] = self._extract_bio(response)
            item['avatar'] = self._extract_avatar(response)
            item['cover_image'] = self._extract_cover_image(response)
            item['is_verified'] = self._extract_verified_status(response)
            item['crawl_time'] = datetime.now()
            
            # 提取统计数据
            item['followers'] = self._extract_followers(response)
            item['following'] = self._extract_following(response)
            item['notes_count'] = self._extract_notes_count(response)
            
            logger.info(f"解析到用户: {item['username']} (ID: {item['user_id']})")
            yield item
            
        except Exception as e:
            logger.error(f"解析用户详情失败: {response.url} - {str(e)}")
            raise
    
    def _extract_user_links(self, response) -> list:
        """提取用户链接"""
        links = []
        
        # 方法1: 通过CSS选择器提取
        css_selectors = [
            'a.user-card::attr(href)',
            'a.author-profile::attr(href)',
            'a[href*="/user/profile/"]::attr(href)',
            'a[href*="/user/"]::attr(href)',
        ]
        
        for selector in css_selectors:
            extracted_links = response.css(selector).getall()
            for link in extracted_links:
                if link.startswith('/'):
                    link = urljoin('https://www.xiaohongshu.com', link)
                if link not in links and self._is_user_url(link):
                    links.append(link)
        
        # 方法2: 通过正则表达式从HTML中提取
        html_content = response.text
        url_patterns = [
            r'https://www\.xiaohongshu\.com/user/profile/[a-zA-Z0-9]+',
            r'https://www\.xiaohongshu\.com/user/[a-zA-Z0-9]+',
        ]
        
        for pattern in url_patterns:
            found_links = re.findall(pattern, html_content)
            for link in found_links:
                if link not in links:
                    links.append(link)
        
        logger.info(f"提取到 {len(links)} 个用户链接")
        return links
    
    def _is_user_url(self, url: str) -> bool:
        """判断是否为用户URL"""
        return any(re.match(pattern, url) for pattern in self.user_url_patterns)
    
    def _extract_user_id(self, url: str) -> str:
        """提取用户ID"""
        # 从URL中提取ID
        if '/user/profile/' in url:
            return url.split('/')[-1]
        elif '/user/' in url:
            return url.split('/')[-1]
        else:
            return ""
    
    def _extract_username(self, response) -> str:
        """提取用户名"""
        # 尝试多种选择器
        selectors = [
            'span.username::text',
            'div.nickname::text',
            'div.user-name::text',
            'h1.user-title::text',
            'meta[property="og:title"]::attr(content)',
        ]
        
        for selector in selectors:
            username = response.css(selector).get()
            if username and username.strip():
                return username.strip()
        
        return ""
    
    def _extract_bio(self, response) -> str:
        """提取个人简介"""
        selectors = [
            'div.user-bio::text',
            'div.bio::text',
            'div.user-desc::text',
            'meta[name="description"]::attr(content)',
        ]
        
        for selector in selectors:
            bio = response.css(selector).get()
            if bio and bio.strip():
                return bio.strip()
        
        # 如果找不到简介，尝试从脚本标签中提取
        script_content = response.css('script[type="text/javascript"]::text').get()
        if script_content:
            # 尝试从JSON数据中提取简介
            try:
                data = json.loads(script_content)
                if 'user' in data:
                    return data['user'].get('bio', '')
            except:
                pass
        
        return ""
    
    def _extract_avatar(self, response) -> str:
        """提取头像链接"""
        selectors = [
            'img.user-avatar::attr(src)',
            'div.avatar img::attr(src)',
            'meta[property="og:image"]::attr(content)',
        ]
        
        for selector in selectors:
            avatar = response.css(selector).get()
            if avatar and avatar.strip():
                # 确保是完整的URL
                avatar = avatar.strip()
                if avatar.startswith('//'):
                    avatar = 'https:' + avatar
                return avatar
        
        return ""
    
    def _extract_cover_image(self, response) -> str:
        """提取封面图片"""
        selectors = [
            'div.cover-image img::attr(src)',
            'div.user-cover img::attr(src)',
            'meta[property="og:image"]::attr(content)',
        ]
        
        for selector in selectors:
            cover = response.css(selector).get()
            if cover and cover.strip():
                # 确保是完整的URL
                cover = cover.strip()
                if cover.startswith('//'):
                    cover = 'https:' + cover
                return cover
        
        return ""
    
    def _extract_verified_status(self, response) -> bool:
        """提取认证状态"""
        selectors = [
            'span.verified-badge::text',
            'div.verified::text',
            'meta[name="verified"]::attr(content)',
        ]
        
        for selector in selectors:
            verified = response.css(selector).get()
            if verified and verified.strip():
                return 'verified' in verified.lower() or '认证' in verified
        
        # 尝试从脚本标签中提取
        script_content = response.css('script[type="text/javascript"]::text').get()
        if script_content:
            try:
                data = json.loads(script_content)
                if 'user' in data:
                    return data['user'].get('is_verified', False)
            except:
                pass
        
        return False
    
    def _extract_followers(self, response) -> int:
        """提取粉丝数"""
        selectors = [
            'span.follower-count::text',
            'div.followers::text',
            'div.stat-item:contains("粉丝")::text',
            'div.user-stats span::text',
        ]
        
        for selector in selectors:
            followers_str = response.css(selector).get()
            if followers_str and followers_str.strip():
                try:
                    # 处理带单位的数据 (如 1.2万)
                    followers_str = followers_str.strip()
                    if '万' in followers_str:
                        return int(float(followers_str.replace('万', '')) * 10000)
                    elif 'k' in followers_str.lower():
                        return int(float(followers_str.lower().replace('k', '')) * 1000)
                    else:
                        return int(followers_str)
                except:
                    continue
        
        return 0
    
    def _extract_following(self, response) -> int:
        """提取关注数"""
        selectors = [
            'span.following-count::text',
            'div.following::text',
            'div.stat-item:contains("关注")::text',
            'div.user-stats span::text',
        ]
        
        for selector in selectors:
            following_str = response.css(selector).get()
            if following_str and following_str.strip():
                try:
                    return int(following_str.strip())
                except:
                    continue
        
        return 0
    
    def _extract_notes_count(self, response) -> int:
        """提取笔记数"""
        selectors = [
            'span.notes-count::text',
            'div.notes::text',
            'div.stat-item:contains("笔记")::text',
            'div.user-stats span::text',
        ]
        
        for selector in selectors:
            notes_str = response.css(selector).get()
            if notes_str and notes_str.strip():
                try:
                    return int(notes_str.strip())
                except:
                    continue
        
        return 0