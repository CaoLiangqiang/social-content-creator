import scrapy
import re
import json
from datetime import datetime
from urllib.parse import urljoin

from ..base.base_crawler import BaseCrawler
from ..utils.logger import logger
from ..items import XiaohongshuCommentItem

class XiaohongshuCommentSpider(BaseCrawler):
    """小红书评论爬虫"""
    
    name = "xiaohongshu_comment"
    platform = "xiaohongshu"
    
    def __init__(self, note_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 设置笔记URL（需要评论的笔记）
        if note_urls:
            if isinstance(note_urls, str):
                self.note_urls = [note_urls]
            else:
                self.note_urls = note_urls
        else:
            # 默认从热门笔记开始
            self.note_urls = [
                'https://www.xiaohongshu.com/explore/example1',
                'https://www.xiaohongshu.com/explore/example2',
            ]
        
        logger.info(f"评论爬虫初始化完成，笔记URL: {self.note_urls}")
    
    def start_requests(self):
        """开始请求"""
        for url in self.note_urls:
            yield self._make_request(url, callback=self.parse_note_page)
    
    def parse_note_page(self, response):
        """解析笔记页面，提取评论"""
        logger.info(f"解析笔记页面: {response.url}")
        
        # 提取评论
        comments = self._extract_comments(response)
        
        for comment in comments:
            yield comment
        
        # 提取分页评论（如果有）
        next_page = self._extract_next_comment_page(response)
        if next_page:
            yield self._make_request(next_page, callback=self.parse_note_page)
    
    def _extract_comments(self, response) -> list:
        """提取评论"""
        comments = []
        
        # 方法1: 通过CSS选择器提取评论
        comment_selectors = [
            'div.comment-item',
            'div.comment-card',
            'div.comment-content',
        ]
        
        for selector in comment_selectors:
            comment_elements = response.css(selector)
            
            for element in comment_elements:
                try:
                    comment = self._parse_single_comment(element)
                    if comment:
                        comments.append(comment)
                except Exception as e:
                    logger.warning(f"解析单个评论失败: {str(e)}")
                    continue
        
        logger.info(f"提取到 {len(comments)} 条评论")
        return comments
    
    def _parse_single_comment(self, comment_element) -> XiaohongshuCommentItem:
        """解析单个评论"""
        item = XiaohongshuCommentItem()
        
        # 提取评论ID
        item['comment_id'] = comment_element.css('::attr(data-comment-id)').get()
        if not item['comment_id']:
            # 如果没有直接ID，生成一个
            item['comment_id'] = str(hash(comment_element.get()))
        
        # 提取评论内容
        content_selectors = [
            'div.comment-text::text',
            'div.content::text',
            'span.comment-content::text',
        ]
        
        for selector in content_selectors:
            content = comment_element.css(selector).get()
            if content and content.strip():
                item['content'] = content.strip()
                break
        
        # 提取评论者信息
        author_selectors = [
            'span.author-name::text',
            'div.author-info a::text',
            'div.nickname::text',
        ]
        
        for selector in author_selectors:
            author = comment_element.css(selector).get()
            if author and author.strip():
                item['author'] = author.strip()
                break
        
        # 提取评论者ID
        author_id_selectors = [
            'span.author-id::text',
            'div.author-info::attr(data-user-id)',
        ]
        
        for selector in author_id_selectors:
            author_id = comment_element.css(selector).get()
            if author_id and author_id.strip():
                item['author_id'] = author_id.strip()
                break
        
        # 提取点赞数
        likes_selectors = [
            'span.like-count::text',
            'div.like-count::text',
        ]
        
        for selector in likes_selectors:
            likes_str = comment_element.css(selector).get()
            if likes_str and likes_str.strip():
                try:
                    # 处理带单位的数据
                    likes_str = likes_str.strip()
                    if '万' in likes_str:
                        item['likes'] = int(float(likes_str.replace('万', '')) * 10000)
                    elif 'k' in likes_str.lower():
                        item['likes'] = int(float(likes_str.lower().replace('k', '')) * 1000)
                    else:
                        item['likes'] = int(likes_str)
                except:
                    item['likes'] = 0
                break
        
        # 提取回复数
        reply_selectors = [
            'span.reply-count::text',
            'div.reply-count::text',
        ]
        
        for selector in reply_selectors:
            reply_str = comment_element.css(selector).get()
            if reply_str and reply_str.strip():
                try:
                    item['reply_count'] = int(reply_str.strip())
                except:
                    item['reply_count'] = 0
                break
        
        # 提取父评论ID（回复功能）
        parent_id = comment_element.css('::attr(data-parent-id)').get()
        if parent_id:
            item['parent_id'] = parent_id
        
        # 设置笔记URL
        item['note_url'] = response.url
        
        # 设置爬取时间
        item['crawl_time'] = datetime.now()
        
        return item
    
    def _extract_next_comment_page(self, response) -> str:
        """提取评论下一页链接"""
        # 尝试通过CSS选择器提取分页链接
        page_selectors = [
            'a.next-page::attr(href)',
            'div.pagination a.next::attr(href)',
            'a.load-more::attr(href)',
        ]
        
        for selector in page_selectors:
            next_page = response.css(selector).get()
            if next_page and next_page.strip():
                if next_page.startswith('/'):
                    next_page = urljoin('https://www.xiaohongshu.com', next_page)
                return next_page.strip()
        
        # 如果找不到分页链接，通过API请求获取更多评论
        api_url = self._build_comment_api_url(response.url)
        if api_url:
            return api_url
        
        return None
    
    def _build_comment_api_url(self, note_url: str) -> str:
        """构建评论API URL"""
        # 从笔记URL中提取笔记ID
        note_id = self._extract_note_id(note_url)
        if not note_id:
            return None
        
        # 构建评论API URL（这是一个示例，实际需要根据小红书API调整）
        api_url = f"https://www.xiaohongshu.com/api/v1/comments?note_id={note_id}&page=1&limit=20"
        return api_url
    
    def _extract_note_id(self, url: str) -> str:
        """从URL中提取笔记ID"""
        if '/explore/' in url:
            return url.split('/')[-1]
        elif '/discovery/item/' in url:
            return url.split('/')[-1]
        else:
            return ""