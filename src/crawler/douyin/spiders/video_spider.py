"""
抖音视频爬虫

> 🎬 抖音视频信息爬取
> 开发者: 智宝 (AI助手)
> 创建日期: 2026-02-12

功能:
- 从视频URL爬取视频信息
- 从创作者主页爬取视频列表
- 从搜索结果爬取视频
- 支持单个视频和批量爬取

技术特点:
- 使用Playwright模拟真实用户
- 自动提取页面JSON数据
- 智能等待和重试
- 完善的错误处理
"""

import asyncio
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import logging

from ..items import DouyinVideoItem, create_video_item_from_json
from ..settings import (
    PLAYWRIGHT_CONFIG,
    RATE_LIMIT_CONFIG,
    DEFAULT_HEADERS,
    EXTRACT_CONFIG
)


logger = logging.getLogger("douyin.video_spider")


class DouyinVideoSpider:
    """
    抖音视频爬虫类
    
    使用Playwright访问抖音页面，从渲染后的页面中提取视频数据。
    完全绕过API签名限制，模拟真实用户行为。
    """
    
    def __init__(self):
        """初始化爬虫"""
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.stats = {
            "success": 0,
            "failed": 0,
            "total": 0
        }
    
    async def __aenter__(self):
        """上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        await self.close()
    
    async def start(self):
        """启动浏览器"""
        logger.info("启动抖音视频爬虫...")
        
        try:
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=PLAYWRIGHT_CONFIG["headless"],
                slow_mo=PLAYWRIGHT_CONFIG["slow_mo"]
            )
            
            # 创建新页面
            self.page = await self.browser.new_page(
                viewport=PLAYWRIGHT_CONFIG["viewport"],
                user_agent=PLAYWRIGHT_CONFIG["user_agent"],
                locale=PLAYWRIGHT_CONFIG["locale"],
                timezone_id=PLAYWRIGHT_CONFIG["timezone"]
            )
            
            # 设置默认超时
            self.page.set_default_timeout(PLAYWRIGHT_CONFIG["timeout"])
            self.page.set_default_navigation_timeout(PLAYWRIGHT_CONFIG["navigation_timeout"])
            
            logger.info("浏览器启动成功")
            
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise
    
    async def close(self):
        """关闭浏览器"""
        logger.info("关闭浏览器...")
        
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("浏览器已关闭")
            
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")
    
    async def crawl_video_by_url(self, url: str) -> Optional[DouyinVideoItem]:
        """
        从URL爬取单个视频
        
        Args:
            url: 视频URL，如 https://www.douyin.com/video/7123456789012345678
            
        Returns:
            DouyinVideoItem对象，失败返回None
        """
        self.stats["total"] += 1
        logger.info(f"开始爬取视频: {url}")
        
        try:
            # 访问页面
            await self._navigate_with_retry(url)
            
            # 等待视频加载
            await self._wait_for_video()
            
            # 提取JSON数据
            json_data = await self._extract_json_data()
            
            if not json_data:
                logger.error("无法提取JSON数据")
                self.stats["failed"] += 1
                return None
            
            # 创建视频对象
            video_item = create_video_item_from_json(json_data)
            
            if video_item and video_item.validate():
                self.stats["success"] += 1
                logger.info(f"视频爬取成功: {video_item.video_id}")
                return video_item
            else:
                logger.error("视频数据验证失败")
                self.stats["failed"] += 1
                return None
                
        except Exception as e:
            logger.error(f"爬取视频失败: {e}")
            self.stats["failed"] += 1
            return None
    
    async def crawl_video_list_by_user(self, user_url: str, max_count: int = 20) -> List[DouyinVideoItem]:
        """
        从创作者主页爬取视频列表
        
        Args:
            user_url: 用户主页URL，如 https://www.douyin.com/user/...
            max_count: 最大爬取数量
            
        Returns:
            视频对象列表
        """
        self.stats["total"] += 1
        logger.info(f"开始爬取用户视频列表: {user_url}")
        
        try:
            videos = []
            
            # 访问用户主页
            await self._navigate_with_retry(user_url)
            
            # 等待页面加载
            await self.page.wait_for_selector("div[data-e2e='user-post-list']", timeout=10000)
            
            # 滚动加载更多视频
            scroll_count = 0
            while len(videos) < max_count and scroll_count < EXTRACT_CONFIG["user_video_max"]:
                # 提取当前页面的视频数据
                json_data = await self._extract_json_data()
                
                if json_data and "aweme_list" in json_data:
                    for video_data in json_data["aweme_list"]:
                        video_item = create_video_item_from_json(video_data)
                        if video_item and video_item.validate():
                            videos.append(video_item)
                            logger.debug(f"提取视频: {video_item.video_id}")
                            
                            if len(videos) >= max_count:
                                break
                
                # 滚动到底部加载更多
                await self._scroll_to_bottom()
                await asyncio.sleep(2)
                
                scroll_count += 1
            
            self.stats["success"] += 1
            logger.info(f"用户视频列表爬取完成，共 {len(videos)} 个视频")
            return videos
            
        except Exception as e:
            logger.error(f"爬取用户视频列表失败: {e}")
            self.stats["failed"] += 1
            return []
    
    async def _navigate_with_retry(self, url: str, max_retries: int = 3):
        """
        带重试的页面导航
        
        Args:
            url: 目标URL
            max_retries: 最大重试次数
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"导航到: {url} (尝试 {attempt + 1}/{max_retries})")
                
                await self.page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 随机延迟，模拟人类
                await asyncio.sleep(2 + attempt)
                
                return
                
            except Exception as e:
                logger.warning(f"导航失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    raise
                else:
                    await asyncio.sleep(5)
    
    async def _wait_for_video(self):
        """等待视频元素加载"""
        try:
            # 等待视频元素出现
            await self.page.wait_for_selector(
                PLAYWRIGHT_CONFIG["wait_selector"],
                timeout=PLAYWRIGHT_CONFIG["video_wait_timeout"]
            )
            
            # 额外等待，确保数据加载完成
            await asyncio.sleep(2)
            
            logger.debug("视频元素加载完成")
            
        except Exception as e:
            logger.warning(f"等待视频元素超时: {e}")
    
    async def _extract_json_data(self) -> Optional[Dict[str, Any]]:
        """
        从页面提取JSON数据
        
        抖音页面将数据存储在 <script id="__RENDER_DATA__"> 标签中
        """
        try:
            # 方法1: 从script标签提取
            script_element = await self.page.query_selector(EXTRACT_CONFIG["json_selector"])
            
            if script_element:
                json_str = await script_element.inner_text()
                
                if json_str:
                    # 解析JSON
                    data = json.loads(json_str)
                    
                    # 提取视频数据
                    if "app" in data and "videoInfo" in data["app"]:
                        return data["app"]["videoInfo"]
                    
                    # 其他可能的数据结构
                    if "aweme_detail" in data:
                        return data["aweme_detail"]
                    
                    logger.debug(f"JSON数据提取成功: {type(data)}")
                    return data
            
            # 方法2: 从window对象提取
            window_data = await self.page.evaluate("""
                () => {
                    // 尝试从window对象获取数据
                    if (window.__INITIAL_STATE__) {
                        return window.__INITIAL_STATE__;
                    }
                    if (window._SSR_HYDRATED_DATA) {
                        return window._SSR_HYDRATED_DATA;
                    }
                    return null;
                }
            """)
            
            if window_data:
                logger.debug("从window对象提取数据成功")
                return window_data
            
            logger.error("无法从页面提取JSON数据")
            return None
            
        except Exception as e:
            logger.error(f"提取JSON数据时出错: {e}")
            return None
    
    async def _scroll_to_bottom(self):
        """滚动到页面底部"""
        try:
            # 平滑滚动
            await self.page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if (totalHeight >= scrollHeight) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            
            logger.debug("滚动到底部完成")
            
        except Exception as e:
            logger.warning(f"滚动失败: {e}")
    
    async def take_screenshot(self, filename: str = None):
        """
        截图（用于调试）
        
        Args:
            filename: 截图文件名
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"douyin_screenshot_{timestamp}.png"
            
            await self.page.screenshot(path=filename)
            logger.info(f"截图已保存: {filename}")
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取爬虫统计信息"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["success"] / self.stats["total"] * 100
                if self.stats["total"] > 0 else 0
            )
        }


# ========== 便捷函数 ==========

async def crawl_single_video(url: str) -> Optional[DouyinVideoItem]:
    """
    爬取单个视频的便捷函数
    
    Args:
        url: 视频URL
        
    Returns:
        DouyinVideoItem对象
    """
    async with DouyinVideoSpider() as spider:
        return await spider.crawl_video_by_url(url)


async def crawl_user_videos(user_url: str, max_count: int = 20) -> List[DouyinVideoItem]:
    """
    爬取用户视频列表的便捷函数
    
    Args:
        user_url: 用户主页URL
        max_count: 最大爬取数量
        
    Returns:
        视频对象列表
    """
    async with DouyinVideoSpider() as spider:
        return await spider.crawl_video_list_by_user(user_url, max_count)


# ========== 测试代码 ==========

async def main():
    """测试代码"""
    # 示例URL（需要替换为真实的抖音视频URL）
    test_url = "https://www.douyin.com/video/7123456789012345678"
    
    print("开始测试抖音视频爬虫...")
    
    async with DouyinVideoSpider() as spider:
        # 爬取单个视频
        video = await spider.crawl_video_by_url(test_url)
        
        if video:
            print(f"\\n视频信息:")
            print(f"ID: {video.video_id}")
            print(f"标题: {video.title}")
            print(f"点赞数: {video.statistics.digg_count}")
            print(f"评论数: {video.statistics.comment_count}")
            print(f"创作者: {video.author.nickname}")
        else:
            print("视频爬取失败")
        
        # 显示统计信息
        stats = spider.get_stats()
        print(f"\\n统计信息: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
