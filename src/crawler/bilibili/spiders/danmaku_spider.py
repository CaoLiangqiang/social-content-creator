"""
B站弹幕爬虫

基于BaseCrawler的B站弹幕数据爬虫
"""

import asyncio
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging
import xml.etree.ElementTree as ET
import requests

from ...base.base_crawler import BaseCrawler, ParseError

logger = logging.getLogger(__name__)


class BilibiliDanmakuSpider(BaseCrawler):
    name = 'bilibili_danmaku'  # Scrapy要求的name属性
    """
    B站弹幕数据爬虫
    
    功能：
    - 爬取B站视频的弹幕
    - 解析XML格式的弹幕文件
    - 处理多种弹幕类型
    """
    
    # 平台配置
    platform = 'bilibili'
    base_url = 'https://www.bilibili.com'
    
    # B站弹幕API端点
    danmaku_api_base = 'https://api.bilibili.com/x/v2/dm'
    danmaku_xml_base = 'https://comment.bilibili.com'
    
    # 速率限制（弹幕API限制较严格）
    rate_limit = 2
    
    # 请求超时
    request_timeout = 10
    
    # User-Agent
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
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
    
    async def crawl_danmaku_by_cid(self, cid: str, aid: str) -> Optional[List[Dict]]:
        """
        通过CID爬取弹幕
        
        Args:
            cid: 视频的CID
            aid: 视频的AV号
            
        Returns:
            弹幕列表
        """
        logger.info(f"[{self.platform}] Crawling danmaku by CID: {cid} (aid: {aid})")
        
        try:
            # 获取弹幕XML文件
            danmaku_xml = await self._get_danmaku_xml(cid, aid)
            
            if not danmaku_xml:
                logger.error(f"Failed to get danmaku XML for CID: {cid}")
                return None
            
            # 解析XML
            danmaku_list = self._parse_danmaku_xml(danmaku_xml, cid, aid)
            
            if danmaku_list:
                logger.info(f"Successfully parsed {len(danmaku_list)} danmaku for CID: {cid}")
                return danmaku_list
            else:
                logger.warning(f"No danmaku found for CID: {cid}")
                return []
                
        except Exception as e:
            logger.error(f"Error crawling danmaku for CID {cid}: {str(e)}")
            return None
    
    async def crawl_realtime_danmaku(
        self,
        aid: str,
        cid: str,
        duration: int = 300,
        interval: int = 30
    ) -> List[Dict]:
        """
        爬取实时弹幕
        
        Args:
            aid: 视频AV号
            cid: 视频CID
            duration: 爬取持续时间（秒）
            interval: 请求间隔（秒）
            
        Returns:
            弹幕列表
        """
        logger.info(f"[{self.platform}] Crawling realtime danmaku for aid: {aid} (cid: {cid})")
        
        danmaku_list = []
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < duration:
            try:
                # 获取实时弹幕
                danmaku_data = await self._get_realtime_danmaku(aid, cid)
                
                if danmaku_data:
                    danmaku_list.extend(danmaku_data)
                    logger.info(f"Got {len(danmaku_data)} realtime danmaku")
                
                # 延迟
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in realtime danmaku crawling: {str(e)}")
                await asyncio.sleep(interval)
                continue
        
        logger.info(f"Realtime danmaku crawling completed: {len(danmaku_list)} danmaku collected")
        return danmaku_list
    
    async def crawl_danmaku_by_video(
        self,
        bvid: str,
        aid: str = None,
        cid: str = None
    ) -> Optional[List[Dict]]:
        """
        通过视频信息爬取弹幕
        
        Args:
            bvid: B站BV号
            aid: 可选的AV号
            cid: 可选的CID（如果未提供会获取）
            
        Returns:
            弹幕列表
        """
        logger.info(f"[{self.platform}] Crawling danmaku by video: {bvid}")
        
        try:
            # 如果没有提供CID，先获取视频信息
            if not cid:
                video_info = await self._get_video_info(bvid, aid)
                if not video_info:
                    logger.error(f"Failed to get video info for {bvid}")
                    return None
                
                cid = video_info.get('cid')
                if not cid:
                    logger.error(f"No CID found for video {bvid}")
                    return None
            
            # 通过CID获取弹幕
            danmaku_list = await self.crawl_danmaku_by_cid(cid, aid or '')
            
            if danmaku_list:
                logger.info(f"Successfully crawled {len(danmaku_list)} danmaku for video {bvid}")
                return danmaku_list
            else:
                logger.warning(f"No danmaku found for video {bvid}")
                return []
                
        except Exception as e:
            logger.error(f"Error crawling danmaku for video {bvid}: {str(e)}")
            return None
    
    async def _get_danmaku_xml(self, cid: str, aid: str) -> Optional[str]:
        """
        获取弹幕XML文件
        
        Args:
            cid: 视频CID
            aid: 视频AV号
            
        Returns:
            XML内容字符串
        """
        try:
            # 构建弹幕XML URL
            xml_url = f"{self.danmaku_xml_base}/{cid}.xml"
            
            # 发起请求
            response = requests.get(
                xml_url,
                headers=self._common_headers,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to get danmaku XML: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting danmaku XML: {str(e)}")
            return None
    
    async def _get_realtime_danmaku(self, aid: str, cid: str) -> Optional[List[Dict]]:
        """
        获取实时弹幕
        
        Args:
            aid: 视频AV号
            cid: 视频CID
            
        Returns:
            弹幕列表
        """
        try:
            # 实时弹幕API
            api_url = f"{self.danmaku_api_base}/web/v2"
            params = {
                'type': 1,
                'oid': aid,
                'oid_str': aid,
                'date': 0,
                'pool': 0,
                'type_1': 0,
                'from_api': 1
            }
            
            response = requests.get(
                api_url,
                params=params,
                headers=self._common_headers,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return self._parse_realtime_danmaku(data, cid, aid)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting realtime danmaku: {str(e)}")
            return None
    
    async def _get_video_info(self, bvid: str, aid: str = None) -> Optional[Dict]:
        """
        获取视频信息
        
        Args:
            bvid: B站BV号
            aid: 可选的AV号
            
        Returns:
            视频信息字典
        """
        try:
            import aiohttp
            
            api_url = f"https://api.bilibili.com/x/web-interface/view"
            params = {'bvid': bvid} if bvid else {'aid': aid}
            
            async with aiohttp.ClientSession(
                headers=self._common_headers,
                timeout=aiohttp.ClientTimeout(total=self.request_timeout)
            ) as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('videoInfo', {})
                    else:
                        return None
                        
        except ImportError:
            # 如果没有aiohttp，使用同步请求
            import requests
            
            try:
                api_url = f"https://api.bilibili.com/x/web-interface/view"
                params = {'bvid': bvid} if bvid else {'aid': aid}
                
                response = requests.get(
                    api_url,
                    params=params,
                    headers=self._common_headers,
                    timeout=self.request_timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('data', {}).get('videoInfo', {})
                else:
                    return None
                    
            except Exception:
                return None
    
    def _parse_danmaku_xml(self, xml_content: str, cid: str, aid: str) -> List[Dict]:
        """
        解析弹幕XML文件
        
        Args:
            xml_content: XML内容
            cid: 视频CID
            aid: 视频AV号
            
        Returns:
            弹幕列表
        """
        try:
            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 找到d标签（弹幕）
            danmaku_list = []
            for d in root.findall('.//d'):
                # 解析弹幕属性
                p = d.get('p', '')
                if not p:
                    continue
                
                # 解析属性字符串，格式：时间,类型,字号,颜色,发送时间,池ID,用户ID,模式
                attrs = p.split(',')
                if len(attrs) < 8:
                    continue
                
                danmaku = {
                    'danmaku_id': f"{aid}_{cid}_{d.get('i', 0)}",
                    'content': d.text or '',
                    'time': float(attrs[0]),
                    'mode': int(attrs[1]),
                    'fontsize': int(attrs[2]),
                    'color': int(attrs[3]),
                    'send_time': int(attrs[4]),
                    'pool': int(attrs[5]),
                    'mid_hash': attrs[6],
                    'crcid': attrs[7] if len(attrs) > 7 else '',
                    'video_id': aid,
                    'cid': cid,
                    'crawl_time': datetime.now().isoformat()
                }
                
                danmaku_list.append(danmaku)
            
            return danmaku_list
            
        except Exception as e:
            logger.error(f"Error parsing danmaku XML: {str(e)}")
            return []
    
    def _parse_realtime_danmaku(self, data: Dict, cid: str, aid: str) -> List[Dict]:
        """
        解析实时弹幕数据
        
        Args:
            data: API响应数据
            cid: 视频CID
            aid: 视频AV号
            
        Returns:
            弹幕列表
        """
        try:
            danmaku_list = []
            
            # 实时弹幕的数据格式与XML不同
            # 这里需要根据实际的API响应来解析
            # 通常包含弹幕内容、时间、类型等信息
            
            comments = data.get('data', {}).get('comments', [])
            
            for comment in comments:
                danmaku = {
                    'danmaku_id': f"{aid}_{cid}_{comment.get('id', 0)}",
                    'content': comment.get('content', ''),
                    'time': comment.get('progress', 0),
                    'mode': 1,  # 默认为滚动弹幕
                    'fontsize': 25,  # 默认字号
                    'color': 16777215,  # 默认颜色（白色）
                    'send_time': comment.get('ctime', 0),
                    'pool': 0,
                    'mid_hash': comment.get('mid_hash', ''),
                    'crcid': '',
                    'video_id': aid,
                    'cid': cid,
                    'crawl_time': datetime.now().isoformat()
                }
                
                danmaku_list.append(danmaku)
            
            return danmaku_list
            
        except Exception as e:
            logger.error(f"Error parsing realtime danmaku: {str(e)}")
            return []
    
    def get_danmaku_stats(self, danmaku_list: List[Dict]) -> Dict:
        """
        获取弹幕统计信息
        
        Args:
            danmaku_list: 弹幕列表
            
        Returns:
            统计信息字典
        """
        if not danmaku_list:
            return {}
        
        stats = {
            'total_count': len(danmaku_list),
            'type_counts': {},
            'time_range': {'start': float('inf'), 'end': float('-inf')},
            'color_counts': {},
            'fontsize_counts': {}
        }
        
        for danmaku in danmaku_list:
            # 统计弹幕类型
            mode = danmaku.get('mode', 0)
            stats['type_counts'][mode] = stats['type_counts'].get(mode, 0) + 1
            
            # 统计时间范围
            time_val = danmaku.get('time', 0)
            if time_val < stats['time_range']['start']:
                stats['time_range']['start'] = time_val
            if time_val > stats['time_range']['end']:
                stats['time_range']['end'] = time_val
            
            # 统计颜色
            color = danmaku.get('color', 0)
            stats['color_counts'][color] = stats['color_counts'].get(color, 0) + 1
            
            # 统计字号
            fontsize = danmaku.get('fontsize', 0)
            stats['fontsize_counts'][fontsize] = stats['fontsize_counts'].get(fontsize, 0) + 1
        
        # 添加平均弹幕密度
        duration = stats['time_range']['end'] - stats['time_range']['start']
        if duration > 0:
            stats['danmaku_per_second'] = stats['total_count'] / duration
        else:
            stats['danmaku_per_second'] = 0
        
        return stats
    
    def filter_danmaku_by_time(
        self,
        danmaku_list: List[Dict],
        start_time: float,
        end_time: float
    ) -> List[Dict]:
        """
        按时间范围过滤弹幕
        
        Args:
            danmaku_list: 弹幕列表
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            
        Returns:
            过滤后的弹幕列表
        """
        return [
            danmaku for danmaku in danmaku_list
            if start_time <= danmaku.get('time', 0) <= end_time
        ]
    
    def filter_danmaku_by_type(
        self,
        danmaku_list: List[Dict],
        mode: int
    ) -> List[Dict]:
        """
        按类型过滤弹幕
        
        Args:
            danmaku_list: 弹幕列表
            mode: 弹幕类型（1=滚动，4=顶部，5=底部）
            
        Returns:
            过滤后的弹幕列表
        """
        return [
            danmaku for danmaku in danmaku_list
            if danmaku.get('mode', 0) == mode
        ]