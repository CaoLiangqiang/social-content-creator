#!/usr/bin/env python3
"""
抖音爬虫单元测试

> 🧪 测试核心功能（不需要真实URL）
> 开发者: 智宝 (AI助手)

测试内容:
- 数据模型创建和验证
- 数据序列化
- 工具函数
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crawler.douyin.items import (
    DouyinVideoItem,
    DouyinCommentItem,
    DouyinUserItem,
    DouyinChallengeItem,
    DouyinStatistics,
    DouyinAuthor,
    DouyinVideoInfo,
    DouyinMusicInfo,
    create_video_item_from_json
)
from datetime import datetime


def test_video_item():
    """测试视频数据模型"""
    print("测试1: DouyinVideoItem...")
    
    # 创建视频对象
    video = DouyinVideoItem(
        video_id="7123456789012345678",
        title="测试视频标题",
        desc="这是一个测试视频",
        create_time=1705094400
    )
    
    # 测试验证
    assert video.validate(), "视频验证失败"
    
    # 测试序列化
    video_dict = video.to_dict()
    assert video_dict["video_id"] == "7123456789012345678"
    assert video_dict["title"] == "测试视频标题"
    
    print("  ✅ DouyinVideoItem创建成功")
    print(f"  ✅ 视频ID: {video.video_id}")
    print(f"  ✅ 标题: {video.title}")
    return True


def test_statistics():
    """测试统计数据模型"""
    print("\\n测试2: DouyinStatistics...")
    
    stats = DouyinStatistics(
        digg_count=1000,
        comment_count=200,
        share_count=50,
        play_count=10000,
        collect_count=150
    )
    
    stats_dict = stats.to_dict()
    assert stats_dict["digg_count"] == 1000
    assert stats_dict["comment_count"] == 200
    
    print("  ✅ DouyinStatistics创建成功")
    print(f"  ✅ 点赞数: {stats.digg_count:,}")
    print(f"  ✅ 评论数: {stats.comment_count:,}")
    return True


def test_author():
    """测试创作者数据模型"""
    print("\\n测试3: DouyinAuthor...")
    
    author = DouyinAuthor(
        uid="123456789",
        nickname="测试用户",
        avatar_thumb="https://example.com/avatar.jpg",
        signature="这是测试签名",
        follower_count=10000,
        following_count=100,
        aweme_count=50,
        verification_type=1
    )
    
    author_dict = author.to_dict()
    assert author_dict["uid"] == "123456789"
    assert author_dict["nickname"] == "测试用户"
    
    print("  ✅ DouyinAuthor创建成功")
    print(f"  ✅ 用户ID: {author.uid}")
    print(f"  ✅ 昵称: {author.nickname}")
    print(f"  ✅ 粉丝数: {author.follower_count:,}")
    return True


def test_comment_item():
    """测试评论数据模型"""
    print("\\n测试4: DouyinCommentItem...")
    
    from src.crawler.douyin.items import DouyinCommentUser
    
    comment = DouyinCommentItem(
        comment_id="comment_123",
        text="这是一条测试评论",
        create_time=1705094400,
        user=DouyinCommentUser(
            uid="user_123",
            nickname="评论用户",
            avatar_thumb="https://example.com/avatar.jpg"
        ),
        digg_count=10,
        reply_comment_total=5,
        aweme_id="7123456789012345678"
    )
    
    # 测试验证
    assert comment.validate(), "评论验证失败"
    
    # 测试序列化
    comment_dict = comment.to_dict()
    assert comment_dict["comment_id"] == "comment_123"
    assert comment_dict["text"] == "这是一条测试评论"
    
    print("  ✅ DouyinCommentItem创建成功")
    print(f"  ✅ 评论ID: {comment.comment_id}")
    print(f"  ✅ 内容: {comment.text}")
    print(f"  ✅ 点赞数: {comment.digg_count}")
    return True


def test_user_item():
    """测试用户数据模型"""
    print("\\n测试5: DouyinUserItem...")
    
    user = DouyinUserItem(
        uid="123456789",
        nickname="测试用户",
        unique_id="testuser",
        signature="测试签名",
        follower_count=10000,
        following_count=100,
        aweme_count=50
    )
    
    # 测试验证
    assert user.validate(), "用户验证失败"
    
    # 测试序列化
    user_dict = user.to_dict()
    assert user_dict["uid"] == "123456789"
    assert user_dict["nickname"] == "测试用户"
    
    print("  ✅ DouyinUserItem创建成功")
    print(f"  ✅ 用户ID: {user.uid}")
    print(f"  ✅ 昵称: {user.nickname}")
    print(f"  ✅ 抖音号: {user.unique_id}")
    return True


def test_challenge_item():
    """测试话题数据模型"""
    print("\\n测试6: DouyinChallengeItem...")
    
    from src.crawler.douyin.items import DouyinChallengeStats
    
    challenge = DouyinChallengeItem(
        cha_id="challenge_123",
        cha_name="测试挑战",
        desc="这是一个测试挑战",
        stats=DouyinChallengeStats(
            view_count=100000,
            join_count=5000,
            video_count=1000
        )
    )
    
    # 测试验证
    assert challenge.validate(), "话题验证失败"
    
    # 测试序列化
    challenge_dict = challenge.to_dict()
    assert challenge_dict["cha_id"] == "challenge_123"
    assert challenge_dict["cha_name"] == "测试挑战"
    
    print("  ✅ DouyinChallengeItem创建成功")
    print(f"  ✅ 话题ID: {challenge.cha_id}")
    print(f"  ✅ 话题名称: {challenge.cha_name}")
    print(f"  ✅ 浏览量: {challenge.stats.view_count:,}")
    return True


def test_create_video_from_json():
    """测试从JSON创建视频对象"""
    print("\\n测试7: create_video_item_from_json...")
    
    # 模拟抖音API返回的JSON数据
    json_data = {
        "aweme_id": "7123456789012345678",
        "desc": "从JSON创建的测试视频",
        "create_time": 1705094400,
        "statistics": {
            "digg_count": 1000,
            "comment_count": 200,
            "share_count": 50,
            "play_count": 10000,
            "collect_count": 150
        },
        "author": {
            "uid": "123456789",
            "nickname": "JSON测试用户",
            "avatar_thumb": {
                "url_list": ["https://example.com/avatar.jpg"]
            },
            "signature": "测试签名",
            "follower_count": 10000,
            "following_count": 100,
            "aweme_count": 50,
            "verification_type": 1
        },
        "video": {
            "play_addr": {
                "url_list": ["https://example.com/video.mp4"]
            },
            "cover": {
                "url_list": ["https://example.com/cover.jpg"]
            },
            "duration": 60000,
            "width": 1920,
            "height": 1080
        },
        "music": {
            "id": "music_123",
            "title": "测试音乐",
            "author": "测试歌手",
            "play_url": {
                "url_list": ["https://example.com/music.mp3"]
            }
        },
        "text_extra": [
            {"hashtag_name": "测试话题1"}
        ],
        "cha_list": [
            {"cha_name": "测试挑战1"}
        ],
        "poi": {
            "poi_name": "测试地点"
        }
    }
    
    # 创建视频对象
    video = create_video_item_from_json(json_data)
    
    # 验证
    assert video is not None, "视频对象创建失败"
    assert video.validate(), "视频验证失败"
    assert video.video_id == "7123456789012345678"
    assert video.title == "从JSON创建的测试视频"
    assert video.statistics.digg_count == 1000
    assert video.author.nickname == "JSON测试用户"
    assert video.video.duration == 60000
    
    print("  ✅ 从JSON创建视频成功")
    print(f"  ✅ 视频ID: {video.video_id}")
    print(f"  ✅ 标题: {video.title}")
    print(f"  ✅ 点赞数: {video.statistics.digg_count:,}")
    print(f"  ✅ 创作者: {video.author.nickname}")
    print(f"  ✅ 时长: {video.video.duration/1000:.1f}秒")
    
    # 测试序列化
    video_dict = video.to_dict()
    assert video_dict["video_id"] == "7123456789012345678"
    print("  ✅ 视频序列化成功")
    
    return True


def test_settings():
    """测试配置模块"""
    print("\\n测试8: Settings模块...")
    
    try:
        from src.crawler.douyin.settings import (
            DOUYIN_BASE_URL,
            RATE_LIMIT_CONFIG,
            PLAYWRIGHT_CONFIG,
            get_config
        )
        
        print(f"  ✅ 配置模块导入成功")
        print(f"  ✅ 抖音基础URL: {DOUYIN_BASE_URL}")
        print(f"  ✅ 速率延迟: {RATE_LIMIT_CONFIG['delay_min']}-{RATE_LIMIT_CONFIG['delay_max']}秒")
        print(f"  ✅ 最大并发: {RATE_LIMIT_CONFIG['max_concurrent']}")
        print(f"  ✅ 无头模式: {PLAYWRIGHT_CONFIG['headless']}")
        
        # 测试配置获取
        config = get_config()
        assert "rate_limit" in config
        assert "storage" in config
        print("  ✅ 配置获取成功")
        
        return True
    except Exception as e:
        print(f"  ❌ 配置模块测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("抖音爬虫单元测试")
    print("="*60)
    print()
    
    tests = [
        ("DouyinVideoItem", test_video_item),
        ("DouyinStatistics", test_statistics),
        ("DouyinAuthor", test_author),
        ("DouyinCommentItem", test_comment_item),
        ("DouyinUserItem", test_user_item),
        ("DouyinChallengeItem", test_challenge_item),
        ("create_video_from_json", test_create_video_from_json),
        ("Settings模块", test_settings)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = passed
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # 打印测试结果
    print("\\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed_count = 0
    failed_count = 0
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if passed:
            passed_count += 1
        else:
            failed_count += 1
    
    print(f"\\n总计: {len(tests)} 个测试")
    print(f"通过: {passed_count} 个")
    print(f"失败: {failed_count} 个")
    print(f"成功率: {passed_count/len(tests)*100:.1f}%")
    
    if failed_count == 0:
        print("\\n🎉 所有测试通过！核心功能正常！")
        print("\\n下一步: 可以使用真实URL测试")
        print("  python3 test_douyin_crawler.py")
        return 0
    else:
        print("\\n⚠️ 部分测试失败，请检查代码")
        return 1


if __name__ == "__main__":
    sys.exit(main())
