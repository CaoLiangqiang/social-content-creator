#!/usr/bin/env python3
"""
数据导出工具

> 📤 将爬取的数据导出为多种格式
> 开发者: 智宝 (AI助手)
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class DataExporter:
    """数据导出器"""

    def __init__(self, output_dir: Path = None):
        """初始化导出器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir or Path.cwd() / 'exports'
        self.output_dir.mkdir(exist_ok=True)

    def export_json(self, data: Dict or List, filename: str = None) -> Path:
        """导出为JSON格式

        Args:
            data: 要导出的数据
            filename: 文件名（不含扩展名）

        Returns:
            导出文件的路径
        """
        if not filename:
            filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def export_csv(self, data: List[Dict], filename: str = None) -> Path:
        """导出为CSV格式

        Args:
            data: 要导出的数据列表
            filename: 文件名（不含扩展名）

        Returns:
            导出文件的路径
        """
        if not filename:
            filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.csv"

        if not data:
            return filepath

        # 获取所有字段
        fieldnames = set()
        for item in data:
            if isinstance(item, dict):
                fieldnames.update(item.keys())

        fieldnames = list(fieldnames)

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for item in data:
                # 处理嵌套字典
                flattened = self._flatten_dict(item)
                writer.writerow(flattened)

        return filepath

    def export_markdown(self, data: List[Dict], filename: str = None, title: str = "数据报告") -> Path:
        """导出为Markdown格式

        Args:
            data: 要导出的数据列表
            filename: 文件名（不含扩展名）
            title: 报告标题

        Returns:
            导出文件的路径
        """
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            for i, item in enumerate(data, 1):
                if not isinstance(item, dict):
                    continue

                f.write(f"## 记录 {i}\n\n")

                # 标题或名称
                for key in ['title', 'name', 'nickname', '标题']:
                    if key in item:
                        f.write(f"**{key}**: {item[key]}\n\n")
                        break

                # 统计数据
                stats_keys = ['play_count', 'like_count', 'digg_count',
                             'comment_count', 'share_count', 'collect_count']

                stats = {k: v for k, v in item.items() if k in stats_keys}

                if stats:
                    f.write("### 📊 统计数据\n\n")
                    for key, value in stats.items():
                        if isinstance(value, (int, float)):
                            f.write(f"{key}: {value:,}\n")
                        else:
                            f.write(f"{key}: {value}\n")
                    f.write("\n")

                # 其他信息
                for key, value in item.items():
                    if key not in stats_keys and key not in ['title', 'name', 'nickname']:
                        f.write(f"**{key}**: {value}\n")

                f.write("---\n\n")

        return filepath

    def export_excel_report(self, bilibili_data: Dict = None,
                          douyin_data: Dict = None,
                          xiaohongshu_data: Dict = None,
                          filename: str = None) -> Path:
        """导出为综合Excel报告（Markdown格式）

        Args:
            bilibili_data: B站数据
            douyin_data: 抖音数据
            xiaohongshu_data: 小红书数据
            filename: 文件名（不含扩展名）

        Returns:
            导出文件的路径
        """
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.output_dir / f"{filename}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 多平台数据报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # B站
            if bilibili_data:
                f.write("## 🎬 B站\n\n")
                self._write_platform_data(f, bilibili_data)
                f.write("\n")

            # 抖音
            if douyin_data:
                f.write("## 🎵 抖音\n\n")
                self._write_platform_data(f, douyin_data)
                f.write("\n")

            # 小红书
            if xiaohongshu_data:
                f.write("## 📕 小红书\n\n")
                self._write_platform_data(f, xiaohongshu_data)
                f.write("\n")

        return filepath

    def _write_platform_data(self, f, data: Dict):
        """写入平台数据到文件"""
        for key, value in data.items():
            if key == 'platform':
                f.write(f"**平台**: {value}\n\n")
            elif key == 'title':
                f.write(f"**标题**: {value}\n\n")
            elif 'count' in key or 'duration' in key:
                if isinstance(value, (int, float)):
                    f.write(f"{key}: {value:,}\n")
                else:
                    f.write(f"{key}: {value}\n")
            elif key in ['author', 'nickname']:
                f.write(f"**{key}**: {value}\n\n")
            elif key == 'tags':
                f.write(f"**标签**: {', '.join(value)}\n" if isinstance(value, list) else f"**标签**: {value}\n")

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """展平嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # 将列表转换为字符串
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)


async def main():
    """测试导出功能"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     数据导出工具测试 - 智宝出品 🌸                        ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 示例数据
    test_data = [
        {
            'platform': 'B站',
            'title': '测试视频1',
            'play_count': 10000,
            'like_count': 500
        },
        {
            'platform': '抖音',
            'title': '测试视频2',
            'digg_count': 2000,
            'comment_count': 100
        }
    ]

    exporter = DataExporter(Path.cwd() / 'exports')

    # 导出JSON
    json_path = exporter.export_json(test_data, 'test_data')
    print(f"✅ JSON导出: {json_path}")

    # 导出CSV
    csv_path = exporter.export_csv(test_data, 'test_data')
    print(f"✅ CSV导出: {csv_path}")

    # 导出Markdown
    md_path = exporter.export_markdown(test_data, 'test_data', '测试报告')
    print(f"✅ Markdown导出: {md_path}")

    print("\n🎉 所有格式导出完成！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
