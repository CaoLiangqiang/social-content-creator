import scrapy
import re
import json
from datetime import datetime
from urllib.parse import urljoin, parse_qs, urlparse

from ..base.base_crawler import BaseCrawler
from ..utils.logger import logger
from ..items import XiaohongshuNoteItem

class XiaohongshuNoteSpider(BaseCrawler):
    """小红书笔记爬虫"""
    
    name = "xiaohongshu_note"
    platform = "xiaohongshu"
    
    # 笔记URL模式
    note_url_patterns = [
        r'https://www\.xiaohongshu\.com/explore/[a-zA-Z0-9]+',
        r'https://www\.xiaohongshu\.com/discovery/item/[a-zA-Z0-9]+',
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
            # 默认从热门笔记开始
            self.start_urls = [
                'https://www.xiaohongshu.com/explore',
                'https://www.xiaohongshu.com/discovery',
            ]
        
        logger.info(f"笔记爬虫初始化完成，起始URL: {self.start_urls}")
    
    def start_requests(self):
        """开始请求"""
        for url in self.start_urls:
            yield self._make_request(url, callback=self.parse_main_page)
    
    def parse_main_page(self, response):
        """解析主页面，提取笔记链接"""
        logger.info(f"解析主页面: {response.url}")
        
        # 提取笔记链接
        note_links = self._extract_note_links(response)
        
        for link in note_links:
            yield self._make_request(link, callback=self.parse_note_detail)
    
    def parse_note_detail(self, response):
        """解析笔记详情"""
        logger.info(f"解析笔记详情: {response.url}")
        
        try:
            # 创建笔记item
            item = XiaohongshuNoteItem()
            
            # 提取基本信息
            item['url'] = response.url
            item['note_id'] = self._extract_note_id(response.url)
            item['title'] = self._extract_title(response)
            item['content'] = self._extract_content(response)
            item['author'] = self._extract_author(response)
            item['author_id'] = self._extract_author_id(response)
            item['publish_time'] = self._extract_publish_time(response)
            item['crawl_time'] = datetime.now()
            
            # 提取互动数据
            item['likes'] = self._extract_likes(response)
            item['comments'] = self._extract_comments(response)
            item['shares'] = self._extract_shares(response)
            
            # 提取标签
            item['tags'] = self._extract_tags(response)
            
            # 提取图片
            item['images'] = self._extract_images(response)
            
            logger.info(f"解析到笔记: {item['title']} (ID: {item['note_id']})")
            yield item
            
        except Exception as e:
            logger.error(f"解析笔记详情失败: {response.url} - {str(e)}")
            raise
    
    def _extract_note_links(self, response) -> list:
        """提取笔记链接"""
        links = []
        
        # 方法1: 通过CSS选择器提取
        css_selectors = [
            'a.explore-feed-card-note::attr(href)',
            'a.note-card::attr(href)',
            'a[href*="/explore/"]::attr(href)',
            'a[href*="/discovery/item/"]::attr(href)',
        ]
        
        for selector in css_selectors:
            extracted_links = response.css(selector).getall()
            for link in extracted_links:
                if link.startswith('/'):
                    link = urljoin('https://www.xiaohongshu.com', link)
                if link not in links and self._is_note_url(link):
                    links.append(link)
        
        # 方法2: 通过正则表达式从HTML中提取
        html_content = response.text
        url_patterns = [
            r'https://www\.xiaohongshu\.com/explore/[a-zA-Z0-9]+',
            r'https://www\.xiaohongshu\.com/discovery/item/[a-zA-Z0-9]+',
        ]
        
        for pattern in url_patterns:
            found_links = re.findall(pattern, html_content)
            for link in found_links:
                if link not in links:
                    links.append(link)
        
        logger.info(f"提取到 {len(links)} 个笔记链接")
        return links
    
    def _is_note_url(self, url: str) -> bool:
        """判断是否为笔记URL"""
        return any(re.match(pattern, url) for pattern in self.note_url_patterns)
    
    def _extract_note_id(self, url: str) -> str:
        """提取笔记ID"""
        # 从URL中提取ID
        if '/explore/' in url:
            return url.split('/')[-1]
        elif '/discovery/item/' in url:
            return url.split('/')[-1]
        else:
            return ''
    
    def _extract_title(self, response) -> str:
        """提取标题"""
        # 尝试多种选择器
        selectors = [
            'h1.note-title::text',
            'h1.title::text',
            'h1.explore-feed-card-title::text',
            'meta[property="og:title"]::attr(content)',
            'title::text',
        ]
        
        for selector in selectors:
            title = response.css(selector).get()
            if title and title.strip():
                return title.strip()
        
        return ""
    
    def _extract_content(self, response) -> str:
        """提取内容"""
        selectors = [
            'div.note-content::text',
            'div.content::text',
            'div.note-detail-content::text',
            'div.explore-feed-card-desc::text',
        ]
        
        for selector in selectors:
            content = response.css(selector).get()
            if content and content.strip():
                return content.strip()
        
        # 如果找不到内容，尝试从脚本标签中提取
        script_content = response.css('script[type="text/javascript"]::text').get()
        if script_content:
            # 尝试从JSON数据中提取内容
            try:
                data = json.loads(script_content)
                if 'note' in data:
                    return data['note'].get('content', '')
            except:
                pass
        
        return ""
    
    def _extract_author(self, response) -> str:
        """提取作者名"""
        selectors = [
            'span.author-name::text',
            'div.author-info a::text',
            'div.nickname::text',
            'meta[property="og:title"]::attr(content)',
        ]
        
        for selector in selectors:
            author = response.css(selector).get()
            if author and author.strip():
                return author.strip()
        
        return ""
    
    def _extract_author_id(self, response) -> str:
        """提取作者ID"""
        selectors = [
            'span.author-id::text',
            'div.author-info::attr(data-user-id)',
            'meta[property="og:description"]::attr(content)',
        ]
        
        for selector in selectors:
            author_id = response.css(selector).get()
            if author_id and author_id.strip():
                return author_id.strip()
        
        return ""
    
    def _extract_publish_time(self, response) -> str:
        """发布时间"""
        selectors = [
            'span.publish-time::text',
            'div.publish-time::text',
            'meta[property="og:published_time"]::attr(content)',
        ]
        
        for selector in selectors:
            time_str = response.css(selector).get()
            if time_str and time_str.strip():
                return time_str.strip()
        
        return ""
    
    def _extract_likes(self, response) -> int:
        """提取点赞数"""
        selectors = [
            'span.like-count::text',
            'div.like-count::text',
            'div.interaction-bar .likes::text',
        ]
        
        for selector in selectors:
            likes_str = response.css(selector).get()
            if likes_str and likes_str.strip():
                try:
                    # 处理带单位的数据 (如 1.2万)
                    likes_str = likes_str.strip()
                    if '万' in likes_str:
                        return int(float(likes_str.replace('万', '')) * 10000)
                    elif 'k' in likes_str.lower():
                        return int(float(likes_str.lower().replace('k', '')) * 1000)
                    else:
                        return int(likes_str)
                except:
                    continue
        
        return 0
    
    def _extract_comments(self, response) -> int:
        """提取评论数"""
        selectors = [
            'span.comment-count::text',
            'div.comment-count::text',
            'div.interaction-bar .comments::text',
        ]
        
        for selector in selectors:
            comments_str = response.css(selector).get()
            if comments_str and comments_str.strip():
                try:
                    return int(comments_str.strip())
                except:
                    continue
        
        return 0
    
    def _extract_shares(self, response) -> int:
        """提取分享数"""
        selectors = [
            'span.share-count::text',
            'div.share-count::text',
            'div.interaction-bar .shares::text',
        ]
        
        for selector in selectors:
            shares_str = response.css(selector).get()
            if shares_str and shares_str.strip():
                try:
                    return int(shares_str.strip())
                except:
                    continue
        
        return 0
    
    def _extract_tags(self, response) -> list:
        """提取标签"""
        tags = []
        
        selectors = [
            'div.tags a::text',
            'div.tag-list span::text',
            'div.note-tags a::text',
        ]
        
        for selector in selectors:
            tag_elements = response.css(selector).getall()
            for tag in tag_elements:
                tag = tag.strip()
                if tag and tag not in tags:
                    tags.append(tag)
        
        return tags
    
    def _extract_images(self, response) -> list:
        """提取图片链接"""
        images = []
        
        selectors = [
            'div.note-content img::attr(src)',
            'div.explore-feed-card img::attr(src)',
            'img.note-image::attr(src)',
        ]
        
        for selector in selectors:
            img_elements = response.css(selector).getall()
            for img in img_elements:
                if img and img.startswith('http'):
                    if img not in images:
                        images.append(img)
        
        return images