#!/usr/bin/env python3
"""
多平台博主每日监控系统

> 支持B站、抖音、小红书等平台
> AI自动总结新内容
> 开发者: 智宝 (AI助手)
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入B站爬虫
from src.crawler.bilibili.bilibili_crawler import BilibiliCrawler


class MultiPlatformMonitor:
    """多平台监控系统"""

    def __init__(self):
        self.data_dir = Path('/home/admin/openclaw/workspace/projects/social-content-creator/data')
        self.data_dir.mkdir(exist_ok=True)

        # 博主数据库
        self.bloggers_file = self.data_dir / 'multi_platform_bloggers.json'
        # 内容记录数据库
        self.content_file = self.data_dir / 'multi_platform_content.json'
        # 每日报告目录
        self.reports_dir = self.data_dir / 'multi_platform_reports'
        self.reports_dir.mkdir(exist_ok=True)

        # Cookie加载
        self.bilibili_cookie = self._load_cookie('bilibili_cookies.json')

    def _load_cookie(self, filename):
        """加载cookie"""
        cookie_file = project_root / filename
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('cookie_string', '')
        return ''

    def load_bloggers(self):
        """加载博主列表"""
        if self.bloggers_file.exists():
            with open(self.bloggers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认博主列表（从之前的测试数据）
            return {
                'bloggers': [
                    # B站 - 使用你之前关注的博主
                    {'platform': 'bilibili', 'name': '老番茄', 'mid': '546195', 'enabled': True},

                    # 可以添加更多博主
                    # {'platform': 'bilibili', 'name': '王赛博', 'mid': '197823715', 'enabled': True},
                ],
                'last_check': None
            }

    def save_bloggers(self, data):
        """保存博主列表"""
        with open(self.bloggers_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_content(self):
        """加载内容记录"""
        if self.content_file.exists():
            with open(self.content_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {'content': {}, 'last_updated': None}

    def save_content(self, data):
        """保存内容记录"""
        with open(self.content_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def get_bilibili_videos(self, mid: str, num: int = 20):
        """获取B站用户最新视频（使用BilibiliCrawler）"""
        try:
            crawler = BilibiliCrawler(cookie_string=self.bilibili_cookie)

            # 获取视频列表
            result = await crawler.get_user_videos(mid, page=1, page_size=num)

            if result and result['videos']:
                videos = []
                for video in result['videos']:
                    videos.append({
                        'id': video.get('bvid', ''),
                        'title': video.get('title', ''),
                        'description': video.get('description', ''),
                        'play': video.get('play', 0),
                        'comment': video.get('comment', 0),
                        'length': video.get('duration', ''),
                        'created': video.get('created', 0),
                        'type': 'video'
                    })
                return videos, None
            else:
                return [], '未获取到视频'

        except Exception as e:
            return None, str(e)

    async def get_douyin_videos(self, user_id: str, num: int = 20):
        """获取抖音用户最新视频（待实现）"""
        return [], '抖音爬虫待实现'

    async def get_xiaohongshu_content(self, user_id: str, num: int = 20):
        """获取小红书用户最新内容"""
        # 从用户上传的JSON文件读取
        xiaohongshu_data_file = self.data_dir / 'xiaohongshu_user_data.json'

        if xiaohongshu_data_file.exists():
            with open(xiaohongshu_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换为监控系统格式
            notes = data.get('notes', [])
            content_list = []

            for note in notes[:num]:
                content_list.append({
                    'id': note.get('note_id', ''),
                    'title': note.get('title', ''),
                    'description': note.get('desc', ''),
                    'liked_count': note.get('liked_count', 0),
                    'collected_count': note.get('collected_count', 0),
                    'comment_count': note.get('comment_count', 0),
                    'created': note.get('time', ''),
                    'type': 'note'
                })

            return content_list, None
        else:
            return [], '未找到小红书数据文件（请先运行xiaohongshu_local_crawler.py并上传数据）'

    async def get_platform_content(self, platform: str, user_id: str):
        """根据平台获取内容"""
        if platform == 'bilibili':
            return await self.get_bilibili_videos(user_id, num=20)
        elif platform == 'douyin':
            return await self.get_douyin_videos(user_id, num=20)
        elif platform == 'xiaohongshu':
            return await self.get_xiaohongshu_content(user_id, num=20)
        else:
            return None, f'未知平台: {platform}'

    def is_new_content(self, content_data, platform: str, content_id: str):
        """检查是否是新内容"""
        key = f"{platform}:{content_id}"

        if key not in content_data['content']:
            return True

        return False

    async def ai_summarize(self, content: dict):
        """使用AI总结内容"""
        title = content.get('title', '')
        description = content.get('description', '')
        play = content.get('play', 0)
        liked_count = content.get('liked_count', 0)

        # 判断热度
        if platform := content.get('platform'):
            if platform == 'bilibili':
                hotness = '热门' if play > 10000 else '普通'
            elif platform == 'xiaohongshu':
                hotness = '热门' if liked_count > 1000 else '普通'
            else:
                hotness = '普通'
        else:
            hotness = '普通'

        # 简单摘要逻辑
        summary = {
            'hotness': hotness,
            'topics': [],
            'summary': (description[:150] + '...') if len(description) > 150 else description or '暂无简介'
        }

        # 提取可能的话题标签
        combined_text = f"{title} {description}"

        if 'AI' in combined_text:
            summary['topics'].append('AI')
        if '教程' in combined_text or 'guide' in combined_text.lower():
            summary['topics'].append('教程')
        if '爬虫' in combined_text or 'crawler' in combined_text.lower():
            summary['topics'].append('爬虫')
        if '自动化' in combined_text or 'automation' in combined_text.lower():
            summary['topics'].append('自动化')

        return summary

    async def check_blogger(self, blogger: dict, content_data: dict):
        """检查单个博主"""
        platform = blogger['platform']
        name = blogger['name']
        user_id = blogger.get('mid') or blogger.get('user_id', '')

        print(f"\n{'='*70}")
        print(f"检查: [{platform.upper()}] {name} (id: {user_id})")
        print('='*70)

        # 获取内容
        content_list, error = await self.get_platform_content(platform, user_id)

        if content_list is None:
            print(f"  ❌ 失败: {error}")
            return [], error

        if not content_list:
            print(f"  ⚠️ 暂无内容: {error}")
            return [], error

        print(f"  ✅ 获取到 {len(content_list)} 条内容")

        # 检查新内容
        new_content = []

        for content in content_list:
            content_id = content['id']

            if self.is_new_content(content_data, platform, content_id):
                # AI总结
                summary = await self.ai_summarize(content)

                new_content.append({
                    'platform': platform,
                    'blogger': name,
                    'content': content,
                    'summary': summary,
                    'discovered_at': datetime.now().isoformat()
                })

                # 更新记录
                key = f"{platform}:{content_id}"
                content_data['content'][key] = {
                    'id': content_id,
                    'title': content['title'],
                    'platform': platform,
                    'blogger': name,
                    'first_seen': datetime.now().isoformat()
                }

                print(f"  ✨ 新内容: {content['title'][:50]}")

        if new_content:
            print(f"\n  🎉 发现 {len(new_content)} 个新内容！")
        else:
            print(f"\n  ℹ️ 暂无新内容")

        return new_content, None

    async def daily_check(self):
        """每日检查"""
        print("="*70)
        print("多平台博主每日监控系统 - 智宝出品")
        print("="*70)

        # 加载数据
        bloggers_data = self.load_bloggers()
        content_data = self.load_content()

        bloggers = [b for b in bloggers_data['bloggers'] if b.get('enabled', True)]

        print(f"\n检查博主数量: {len(bloggers)}")

        # 如果有B站博主，等待频率限制冷却
        bilibili_bloggers = [b for b in bloggers if b['platform'] == 'bilibili']
        if bilibili_bloggers:
            print("\n⏳ 等待30秒让B站API频率限制冷却...")
            await asyncio.sleep(30)

        # 按平台分组
        by_platform = {}
        for blogger in bloggers:
            platform = blogger['platform']
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(blogger)

        print(f"平台分布: {', '.join([f'{p}:{len(by_platform[p])}' for p in by_platform])}")

        all_new_content = []
        errors = []

        # 检查每个博主
        for i, blogger in enumerate(bloggers, 1):
            print(f"\n进度: [{i}/{len(bloggers)}]")

            new_content, error = await self.check_blogger(blogger, content_data)

            if new_content:
                all_new_content.extend(new_content)

            if error:
                errors.append({
                    'blogger': blogger['name'],
                    'platform': blogger['platform'],
                    'error': error
                })

            # B站需要等待避免频率限制
            if blogger['platform'] == 'bilibili' and i < len(bloggers):
                print(f"\n⏳ 等待90秒后继续...")
                await asyncio.sleep(90)  # 增加到90秒

        # 保存内容记录
        content_data['last_updated'] = datetime.now().isoformat()
        self.save_content(content_data)

        # 更新最后检查时间
        bloggers_data['last_check'] = datetime.now().isoformat()
        self.save_bloggers(bloggers_data)

        # 生成日报
        if all_new_content or errors:
            await self.generate_daily_report(all_new_content, errors)
        else:
            print("\n" + "="*70)
            print("今日无新内容")
            print("="*70)

        return all_new_content, errors

    async def generate_daily_report(self, new_content, errors):
        """生成日报"""
        today = datetime.now().strftime('%Y-%m-%d')
        report_file = self.reports_dir / f'{today}.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 多平台博主日报\n\n")
            f.write(f"**日期**: {today}\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%H:%M:%S')}\n\n")
            f.write("---\n\n")

            # 按平台分组
            by_platform = {}
            for item in new_content:
                platform = item['platform']
                if platform not in by_platform:
                    by_platform[platform] = []
                by_platform[platform].append(item)

            # 统计
            f.write("## 📊 今日统计\n\n")
            f.write(f"- **新内容数量**: {len(new_content)}\n")
            f.write(f"- **涉及平台**: {len(by_platform)}\n")

            for platform, items in by_platform.items():
                f.write(f"- **{platform.upper()}**: {len(items)} 条\n")

            f.write("\n")

            # 按平台展示
            platform_names = {
                'bilibili': '📺 B站',
                'douyin': '🎵 抖音',
                'xiaohongshu': '📕 小红书'
            }

            for platform in ['bilibili', 'douyin', 'xiaohongshu']:
                if platform not in by_platform:
                    continue

                items = by_platform[platform]

                f.write(f"## {platform_names.get(platform, platform.upper())}\n\n")

                for item in items:
                    summary = item['summary']
                    content = item['content']

                    f.write(f"### {content['title']}\n\n")
                    f.write(f"**博主**: {item['blogger']}\n")
                    f.write(f"**热度**: {summary['hotness']} | ")

                    if content.get('play'):
                        f.write(f"**播放**: {content['play']:,} | ")
                        f.write(f"**评论**: {content.get('comment', 0):,}\n\n")
                    elif content.get('liked_count'):
                        f.write(f"**点赞**: {content['liked_count']:,} | ")
                        f.write(f"**收藏**: {content.get('collected_count', 0):,}\n\n")
                    else:
                        f.write("\n")

                    # AI摘要
                    f.write(f"**AI摘要**: {summary['summary']}\n")

                    if summary['topics']:
                        f.write(f"**话题标签**: {', '.join(summary['topics'])}\n")

                    f.write(f"\n---\n\n")

            # 错误报告
            if errors:
                f.write("## ⚠️ 检查错误\n\n")

                for error in errors:
                    f.write(f"- [{error['platform'].upper()}] **{error['blogger']}**: {error['error']}\n")

                f.write("\n")

        print(f"\n✅ 日报已生成: {report_file}")

        # 生成简短摘要
        summary_file = self.reports_dir / f'{today}_summary.txt'

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"多平台博主日报 - {today}\n")
            f.write("="*70 + "\n\n")

            if new_content:
                f.write(f"🎉 今日发现 {len(new_content)} 条新内容\n\n")

                for item in new_content:
                    platform = item['platform'].upper()
                    blogger = item['blogger']
                    title = item['content']['title']

                    f.write(f"[{platform}] {blogger}: {title}\n")
            else:
                f.write("今日暂无新内容\n")

            if errors:
                f.write(f"\n⚠️ {len(errors)} 个博主检查失败\n")

        print(f"✅ 摘要已生成: {summary_file}")


async def main():
    """主函数"""
    monitor = MultiPlatformMonitor()

    # 执行每日检查
    new_content, errors = await monitor.daily_check()

    print("\n" + "="*70)
    print("检查完成！")
    print("="*70)

    print(f"\n新内容: {len(new_content)}")
    print(f"错误: {len(errors)}")

    if new_content:
        print("\n✨ 发现新内容，日报已生成！")
        print(f"📁 查看日报: {monitor.reports_dir / datetime.now().strftime('%Y-%m-%d') + '.md'}")


if __name__ == "__main__":
    asyncio.run(main())
