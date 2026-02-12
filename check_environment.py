#!/usr/bin/env python3
"""
环境检查脚本

检查抖音爬虫所需的所有依赖
"""

import sys
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要Python 3.8+")
        return False


def check_playwright():
    """检查Playwright安装"""
    print("\\n检查Playwright...")
    try:
        import playwright
        print("✅ Playwright已安装")
        return True
    except ImportError:
        print("❌ Playwright未安装")
        print("   安装命令: pip install playwright")
        return False


def check_playwright_browsers():
    """检查Playwright浏览器"""
    print("\\n检查Playwright浏览器...")
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright浏览器模块可用")
        return True
    except ImportError as e:
        print(f"❌ Playwright浏览器模块不可用: {e}")
        print("   安装命令: playwright install chromium")
        return False


def check_asyncio():
    """检查asyncio支持"""
    print("\\n检查asyncio支持...")
    try:
        import asyncio
        print("✅ asyncio可用")
        return True
    except ImportError:
        print("❌ asyncio不可用")
        return False


def check_project_structure():
    """检查项目结构"""
    print("\\n检查项目结构...")
    
    project_root = Path(__file__).parent
    required_paths = [
        project_root / "src" / "crawler" / "douyin" / "__init__.py",
        project_root / "src" / "crawler" / "douyin" / "items.py",
        project_root / "src" / "crawler" / "douyin" / "settings.py",
        project_root / "src" / "crawler" / "douyin" / "spiders" / "video_spider.py",
    ]
    
    all_exist = True
    for path in required_paths:
        if path.exists():
            print(f"✅ {path.relative_to(project_root)}")
        else:
            print(f"❌ {path.relative_to(project_root)} (不存在)")
            all_exist = False
    
    return all_exist


def main():
    """主检查函数"""
    print("="*60)
    print("抖音爬虫环境检查")
    print("="*60)
    
    results = {
        "Python版本": check_python_version(),
        "Playwright": check_playwright(),
        "Playwright浏览器": check_playwright_browsers(),
        "asyncio": check_asyncio(),
        "项目结构": check_project_structure()
    }
    
    print("\\n" + "="*60)
    print("检查结果汇总")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\\n🎉 所有检查通过！环境已准备好！")
        print("\\n下一步: 运行测试脚本")
        print("  python3 test_douyin_crawler.py")
        return 0
    else:
        print("\\n⚠️ 部分检查未通过，请修复上述问题")
        failed = [name for name, passed in results.items() if not passed]
        print(f"\\n需要修复: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
