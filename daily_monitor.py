#!/usr/bin/env python3
"""
B站博主每日监控系统

> 每天检查博主新视频并生成日报
> 开发者: 智宝 (AI助手)
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


class BloggerMonitor:
    """博主监控系统"""

    def __init__(self):
        self.data_dir = Path('/home/admin/openclaw/workspace/projects/social-content-creator/data')
        self.data_dir.mkdir(exist_ok=True)

        # 博主数据库
        self.bloggers_file = self.data_dir / 'bloggers.json'
        # 视频记录数据库
        self.videos_file = self.data_dir / 'videos.json'
        # 每日报告目录
        self.reports_dir = self.data_dir / 'daily_reports'
        self.reports_dir.mkdir(exist_ok=True)

    def load_bloggers(self):
        """加载博主列表"""
        if self.bloggers_file.exists():
            with open(self.bloggers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认博主列表
            return {
                'bloggers': [
                    {'name': '老戴Donald', 'mid': '3493075691243699', 'enabled': True},
                    {'name': 'AI超元域', 'mid': '3493277319825652', 'enabled': True},
                    {'name': '王赛博', 'mid': '197823715', 'enabled': True},
                    {'name': '工科男孙老师', 'mid': '43584648', 'enabled': True},
                    {'name': '芯板坊', 'mid': '2097113874', 'enabled': True},
                    {'name': '秋芝2046', 'mid': '385670211', 'enabled': True}
                ],
                'last_check': None
            }

    def save_bloggers(self, data):
        """保存博主列表"""
        with open(self.bloggers_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_videos(self):
        """加载视频记录"""
        if self.videos_file.exists():
            with open(self.videos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {'videos': {}, 'last_updated': None}

    def save_videos(self, data):
        """保存视频记录"""
        with open(self.videos_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def get_user_videos(self, session, mid: str, num: int = 10):
        """
        获取用户最新视频

        使用稳定的请求策略：
        - 完整的浏览器headers
        - 持久化session
        - 充足的延迟
        """
        url = "https://api.bilibili.com/x/space/arc/search"
        params = {'mid': mid, 'ps': num, 'pn': 1}

        # 使用完整的浏览器headers，模拟真实请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'https://space.bilibili.com/{mid}/video',
            'Origin': 'https://space.bilibili.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }

        try:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json()

                if data.get('code') == 0:
                    vlist = data['data']['list']['vlist']
                    videos = []

                    for item in vlist[:num]:
                        video = {
                            'bvid': item.get('bvid', ''),
                            'title': item.get('title', ''),
                            'description': item.get('description', ''),
                            'play': item.get('play', 0),
                            'comment': item.get('comment', 0),
                            'length': item.get('length', ''),
                            'created': item.get('created', 0),
                            'pic': item.get('pic', '')
                        }
                        videos.append(video)

                    return videos, None
                else:
                    return None, data.get('message', '未知错误')

        except asyncio.TimeoutError:
            return None, '请求超时'
        except Exception as e:
            return None, str(e)

    def is_new_video(self, videos_data, bvid: str, created: int):
        """检查是否是新视频"""
        # 如果视频记录中不存在，就是新视频
        if bvid not in videos_data['videos']:
            return True

        # 检查创建时间是否更新（可能是重新上传）
        existing = videos_data['videos'][bvid]
        if existing.get('created', 0) != created:
            return True

        return False

    async def check_blogger(self, session, blogger: dict, videos_data: dict):
        """检查单个博主"""
        name = blogger['name']
        mid = blogger['mid']

        print(f"\n{'='*70}")
        print(f"检查: {name} (mid: {mid})")
        print('='*70)

        # 获取最新视频
        videos, error = await self.get_user_videos(session, mid, num=20)  # 获取20个确保覆盖

        if videos:
            new_videos = []

            for video in videos:
                bvid = video['bvid']
                created = video['created']

                # 检查是否是新视频
                if self.is_new_video(videos_data, bvid, created):
                    new_videos.append(video)
                    print(f"  ✨ 新视频: {video['title'][:50]}")

                    # 更新视频记录
                    videos_data['videos'][bvid] = {
                        'bvid': bvid,
                        'title': video['title'],
                        'created': created,
                        'blogger': name,
                        'first_seen': datetime.now().isoformat()
                    }

            if new_videos:
                print(f"\n  🎉 发现 {len(new_videos)} 个新视频！")
            else:
                print(f"\n  ℹ️ 暂无新视频")

            return new_videos, None
        else:
            print(f"  ❌ 失败: {error}")
            return [], error

    async def daily_check(self):
        """每日检查"""
        print("="*70)
        print("B站博主每日监控系统 - 智宝出品")
        print("="*70)

        # 加载数据
        bloggers_data = self.load_bloggers()
        videos_data = self.load_videos()

        bloggers = [b for b in bloggers_data['bloggers'] if b.get('enabled', True)]

        print(f"\n检查博主数量: {len(bloggers)}")

        # 创建持久化session
        connector = aiohttp.TCPConnector(limit=3, limit_per_host=1)  # 非常保守的连接限制
        timeout = aiohttp.ClientTimeout(total=30, connect=10)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        all_new_videos = []
        errors = []

        async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=timeout) as session:
            for i, blogger in enumerate(bloggers, 1):
                print(f"\n进度: [{i}/{len(bloggers)}]")

                new_videos, error = await self.check_blogger(session, blogger, videos_data)

                if new_videos:
                    all_new_videos.extend(new_videos)

                if error:
                    errors.append({
                        'blogger': blogger['name'],
                        'error': error
                    })

                # 每个博主之间等待60秒（避免限流）
                if i < len(bloggers):
                    print(f"\n⏳ 等待60秒后继续...")
                    await asyncio.sleep(60)

        # 保存视频记录
        videos_data['last_updated'] = datetime.now().isoformat()
        self.save_videos(videos_data)

        # 更新最后检查时间
        bloggers_data['last_check'] = datetime.now().isoformat()
        self.save_bloggers(bloggers_data)

        # 生成日报
        if all_new_videos or errors:
            await self.generate_daily_report(all_new_videos, errors)
        else:
            print("\n" + "="*70)
            print("今日无新视频")
            print("="*70)

        return all_new_videos, errors

    async def generate_daily_report(self, new_videos, errors):
        """生成日报"""
        today = datetime.now().strftime('%Y-%m-%d')
        report_file = self.reports_dir / f'{today}.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# B站科技博主日报\n\n")
            f.write(f"**日期**: {today}\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%H:%M:%S')}\n\n")
            f.write("---\n\n")

            # 新视频统计
            if new_videos:
                f.write(f"## 📊 今日统计\n\n")
                f.write(f"- **新视频数量**: {len(new_videos)}\n")

                # 按博主分组
                by_blogger = {}
                for video in new_videos:
                    blogger = video.get('blogger', '未知')
                    if blogger not in by_blogger:
                        by_blogger[blogger] = []
                    by_blogger[blogger].append(video)

                f.write(f"- **涉及博主**: {len(by_blogger)}\n\n")

                # 新视频列表
                f.write("## 🆕 新视频列表\n\n")

                for blogger, videos in by_blogger.items():
                    f.write(f"### {blogger}\n\n")
                    f.write(f"**数量**: {len(videos)}\n\n")

                    for video in videos:
                        f.write(f"#### {video['title']}\n\n")
                        f.write(f"**BVID**: {video['bvid']}\n")
                        f.write(f"**时长**: {video['length']} | **播放**: {video['play']:,}\n")
                        f.write(f"**发布时间**: {datetime.fromtimestamp(video['created']).strftime('%Y-%m-%d %H:%M')}\n\n")

                        if video.get('description'):
                            f.write(f"**简介**: {video['description'][:150]}...\n\n")

                        f.write("---\n\n")

            # 错误报告
            if errors:
                f.write("## ⚠️ 检查错误\n\n")

                for error in errors:
                    f.write(f"- **{error['blogger']}**: {error['error']}\n")

                f.write("\n")

        print(f"\n✅ 日报已生成: {report_file}")

        # 同时生成摘要
        summary_file = self.reports_dir / f'{today}_summary.txt'

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"B站科技博主日报 - {today}\n")
            f.write("="*70 + "\n\n")

            if new_videos:
                f.write(f"🎉 今日发现 {len(new_videos)} 个新视频\n\n")

                for video in new_videos:
                    f.write(f"• [{video.get('blogger', '未知')}] {video['title'][:50]}\n")
            else:
                f.write("今日暂无新视频\n")

            if errors:
                f.write(f"\n⚠️ {len(errors)} 个博主检查失败\n")

        print(f"✅ 摘要已生成: {summary_file}")


async def main():
    """主函数"""
    monitor = BloggerMonitor()

    # 执行每日检查
    new_videos, errors = await monitor.daily_check()

    print("\n" + "="*70)
    print("检查完成！")
    print("="*70)

    print(f"\n新视频: {len(new_videos)}")
    print(f"错误: {len(errors)}")


if __name__ == "__main__":
    asyncio.run(main())
