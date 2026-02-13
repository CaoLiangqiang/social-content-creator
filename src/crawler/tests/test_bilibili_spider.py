"""
B站爬虫单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bilibili.spider import BilibiliSpider, CrawlerConfig


class TestBilibiliSpider:
    """B站爬虫测试类"""
    
    @pytest.fixture
    def spider(self):
        """创建爬虫实例"""
        config = CrawlerConfig(timeout=30, delay=0.1)
        return BilibiliSpider(config)
    
    @pytest.fixture
    def mock_session(self):
        """Mock HTTP会话"""
        with patch('aiohttp.ClientSession') as mock:
            yield mock
    
    def test_validate_bvid_valid(self, spider):
        """测试有效BV号验证"""
        valid_bvids = [
            "BV1xx411c7mD",
            "BV1ab2cd3ef4",
            "BV1234567890"
        ]
        for bvid in valid_bvids:
            assert spider._validate_bvid(bvid) is True, f"{bvid} should be valid"
    
    def test_validate_bvid_invalid(self, spider):
        """测试无效BV号验证"""
        invalid_bvids = [
            "invalid",
            "BV123",  # 太短
            "1234567890",  # 没有BV前缀
            "BV12345678901",  # 太长
            "",  # 空字符串
            None  # None
        ]
        for bvid in invalid_bvids:
            assert spider._validate_bvid(bvid) is False, f"{bvid} should be invalid"
    
    def test_validate_mid_valid(self, spider):
        """测试有效MID验证"""
        valid_mids = ["123456", "0", "999999999"]
        for mid in valid_mids:
            assert spider._validate_mid(mid) is True, f"{mid} should be valid"
    
    def test_validate_mid_invalid(self, spider):
        """测试无效MID验证"""
        invalid_mids = ["abc", "12.34", "", None, "12a34"]
        for mid in invalid_mids:
            assert spider._validate_mid(mid) is False, f"{mid} should be invalid"
    
    @pytest.mark.asyncio
    async def test_fetch_video_invalid_bvid(self, spider):
        """测试无效BV号抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            async with spider:
                await spider.fetch_video("invalid")
        
        assert "Invalid BVID" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_user_invalid_mid(self, spider):
        """测试无效MID抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            async with spider:
                await spider.fetch_user("invalid")
        
        assert "Invalid MID" in str(exc_info.value)
    
    def test_parse_video_data(self, spider):
        """测试视频数据解析"""
        raw_data = {
            "bvid": "BV1xx411c7mD",
            "title": "测试视频",
            "desc": "这是一个测试视频",
            "owner": {
                "mid": 123456,
                "name": "测试UP",
                "face": "https://example.com/avatar.jpg"
            },
            "stat": {
                "view": 10000,
                "like": 500,
                "reply": 100,
                "share": 50,
                "favorite": 200
            },
            "pic": "https://example.com/cover.jpg",
            "tags": [
                {"tag_name": "测试"},
                {"tag_name": "视频"}
            ],
            "pubdate": 1609459200,
            "duration": 300
        }
        
        result = spider._parse_video_data(raw_data)
        
        assert result["platform_id"] == 1
        assert result["platform_content_id"] == "BV1xx411c7mD"
        assert result["title"] == "测试视频"
        assert result["content"] == "这是一个测试视频"
        assert result["author_id"] == "123456"
        assert result["author_name"] == "测试UP"
        assert result["view_count"] == 10000
        assert result["like_count"] == 500
        assert result["comment_count"] == 100
        assert result["tags"] == ["测试", "视频"]
        assert "crawled_at" in result
    
    def test_parse_user_data(self, spider):
        """测试用户数据解析"""
        raw_data = {
            "mid": 123456,
            "name": "测试用户",
            "face": "https://example.com/avatar.jpg",
            "sign": "测试签名",
            "follower": 10000,
            "following": 100,
            "level": 6
        }
        
        result = spider._parse_user_data(raw_data)
        
        assert result["platform_id"] == 1
        assert result["platform_user_id"] == "123456"
        assert result["username"] == "测试用户"
        assert result["description"] == "测试签名"
        assert result["followers_count"] == 10000
        assert result["level"] == 6
    
    def test_parse_search_result(self, spider):
        """测试搜索结果解析"""
        raw_data = {
            "bvid": "BV1xx411c7mD",
            "title": "<em class=\"keyword\">测试</em>视频",
            "description": "测试描述",
            "author": "测试UP",
            "play": 5000,
            "like": 300,
            "pic": "https://example.com/cover.jpg",
            "pubdate": 1609459200,
            "duration": "5:00",
            "tag": "测试,视频,标签"
        }
        
        result = spider._parse_search_result(raw_data)
        
        assert result["platform_content_id"] == "BV1xx411c7mD"
        assert "<em" not in result["title"]  # HTML标签应该被移除
        assert result["author_name"] == "测试UP"
        assert result["view_count"] == 5000
        assert result["tags"] == ["测试", "视频", "标签"]
    
    def test_parse_comment(self, spider):
        """测试评论数据解析"""
        raw_data = {
            "rpid": 123456789,
            "content": {"message": "测试评论"},
            "member": {
                "uname": "评论用户",
                "avatar": "https://example.com/avatar.jpg"
            },
            "like": 50,
            "rcount": 10,
            "ctime": 1609459200,
            "top": True
        }
        
        result = spider._parse_comment(raw_data)
        
        assert result["comment_id"] == "123456789"
        assert result["content"] == "测试评论"
        assert result["author_name"] == "评论用户"
        assert result["like_count"] == 50
        assert result["reply_count"] == 10
        assert result["is_top"] is True


class TestCrawlerConfig:
    """爬虫配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = CrawlerConfig()
        assert config.timeout == 30
        assert config.retry_count == 3
        assert config.delay == 1.0
        assert config.proxy is None
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = CrawlerConfig(
            timeout=60,
            retry_count=5,
            delay=2.0,
            proxy="http://proxy.example.com:8080"
        )
        assert config.timeout == 60
        assert config.retry_count == 5
        assert config.delay == 2.0
        assert config.proxy == "http://proxy.example.com:8080"
