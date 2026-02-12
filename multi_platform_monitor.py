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

    def load_bloggers(self):
        """加载博主列表"""
        if self.bloggers_file.exists():
            with open(self.bloggers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认博主列表（多平台）
            return {
                'bloggers': [
                    # B站
                    {'platform': 'bilibili', 'name': '王赛博', 'mid': '197823715', 'enabled': True},
                    {'platform': 'bilibili', 'name': 'AI超元域', 'mid': '3493277319825652', 'enabled': True},

                    # 抖音（示例）
                    {'platform': 'douyin', 'name': '未来奇点', 'user_id': '7605649587327569202', 'enabled': True},

                    # 小红书（示例）
                    {'platform': 'xiaohongshu', 'name': '示例博主', 'user_id': 'example', 'enabled': False}
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

    async def get_bilibili_videos(self, session, mid: str, num: int = 10):
        """获取B站用户最新视频"""
        url = "https://api.bilibili.com/x/space/arc/search"
        params = {'mid': mid, 'ps': num, 'pn': 1}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'https://space.bilibili.com/{mid}/video',
        }

        try:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json()

                if data.get('code') == 0:
                    vlist = data['data']['list']['vlist']
                    content_list = []

                    for item in vlist[:num]:
                        content = {
                            'id': item.get('bvid', ''),
                            'title': item.get('title', ''),
                            'description': item.get('description', ''),
                            'play': item.get('play', 0),
                            'comment': item.get('comment', 0),
                            'length': item.get('length', ''),
                            'created': item.get('created', 0),
                            'type': 'video'
                        }
                        content_list.append(content)

                    return content_list, None
                else:
                    return None, data.get('message', '未知错误')

        except Exception as e:
            return None, str(e)

    async def get_douyin_videos(self, session, user_id: str, num: int = 10):
        """获取抖音用户最新视频（基础版本）"""
        # 注意：抖音需要更复杂的处理，这里先做基础框架
        # 实际需要调用抖音爬虫

        # 暂时返回空列表，等待实际实现
        return [], '抖音爬虫待实现'

    async def get_xiaohongshu_content(self, session, user_id: str, num: int = 10):
        """获取小红书用户最新内容（基础版本）"""
        # 注意：小红书需要content_id，这里先做基础框架
        # 实际需要调用小红书爬虫

        # 暂时返回空列表，等待实际实现
        return [], '小红书爬虫待实现'

    async def get_platform_content(self, session, platform: str, user_id: str):
        """根据平台获取内容"""
        if platform == 'bilibili':
            return await self.get_bilibili_videos(session, user_id, num=20)
        elif platform == 'douyin':
            return await self.get_douyin_videos(session, user_id, num=20)
        elif platform == 'xiaohongshu':
            return await self.get_xiaohongshu_content(session, user_id, num=20)
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
        # 基础版本：简单提取关键信息
        # 后续可以接入真正的AI API

        title = content.get('title', '')
        description = content.get('description', '')
        play = content.get('play', 0)

        # 简单摘要逻辑
        summary = {
            'type': 'video',
            'title': title,
            'hotness': '热门' if play > 10000 else '普通',
            'topics': [],
            'summary': description[:200] if description else '暂无简介'
        }

        # 提取可能的话题标签
        if 'AI' in title or 'AI' in description:
            summary['topics'].append('AI')
        if '教程' in title or '教程' in description:
            summary['topics'].append('教程')
        if 'N8N' in title or '爬虫' in title:
            summary['topics'].append('自动化')

        return summary

    async def check_blogger(self, session, blogger: dict, content_data: dict):
        """检查单个博主"""
        platform = blogger['platform']
        name = blogger['name']
        user_id = blogger.get('mid') or blogger.get('user_id', '')

        print(f"\n{'='*70}")
        print(f"检查: [{platform.upper()}] {name} (id: {user_id})")
        print('='*70)

        # 获取内容
        content_list, error = await self.get_platform_content(session, platform, user_id)

        if content_list is None:
            print(f"  ❌ 失败: {error}")
            return [], error

        if not content_list:
            print(f"  ⚠️ 暂无内容: {error}")
            return [], error

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

        # 按平台分组
        by_platform = {}
        for blogger in bloggers:
            platform = blogger['platform']
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(blogger)

        print(f"平台分布: {', '.join([f'{p}:{len(by_platform[p])}' for p in by_platform])}")

        # 创建持久化session
        connector = aiohttp.TCPConnector(limit=3, limit_per_host=1)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        all_new_content = []
        errors = []

        async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=timeout) as session:
            for i, blogger in enumerate(bloggers, 1):
                print(f"\n进度: [{i}/{len(bloggers)}]")

                new_content, error = await self.check_blogger(session, blogger, content_data)

                if new_content:
                    all_new_content.extend(new_content)

                if error:
                    errors.append({
                        'blogger': blogger['name'],
                        'platform': blogger['platform'],
                        'error': error
                    })

                # 每个博主之间等待60秒
                if i < len(bloggers):
                    print(f"\n⏳ 等待60秒后继续...")
                    await asyncio.sleep(60)

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
            for platform in ['bilibili', 'douyin', 'xiaohongshu']:
                if platform not in by_platform:
                    continue

                items = by_platform[platform]

                f.write(f"## 📱 {platform.upper()}\n\n")

                for item in items:
                    summary = item['summary']
                    content = item['content']

                    f.write(f"### {summary['title']}\n\n")
                    f.write(f"**博主**: {item['blogger']}\n")
                    f.write(f"**热度**: {summary['hotness']} | ")

                    if content.get('play'):
                        f.write(f"**播放**: {content['play']:,}\n")
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
                    title = item['summary']['title']

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


if __name__ == "__main__":
    asyncio.run(main())
