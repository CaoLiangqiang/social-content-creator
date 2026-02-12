#!/usr/bin/env python3
"""
抖音页面分析工具

> 🔍 分析抖音页面结构
> 开发者: 智宝 (AI助手)
"""

import requests
import re
import json
from bs4 import BeautifulSoup


def analyze_douyin_page(url):
    """分析抖音页面"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    }
    
    print("访问页面...")
    response = requests.get(url, headers=headers, allow_redirects=True)
    
    print(f"状态码: {response.status_code}")
    print(f"最终URL: {response.url}")
    print(f"内容长度: {len(response.text)}")
    
    # 保存完整HTML
    with open('/tmp/douyin_full.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("完整HTML已保存到 /tmp/douyin_full.html")
    
    # 解析
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 查找所有script
    scripts = soup.find_all('script')
    print(f"\\n找到 {len(scripts)} 个script标签")
    
    # 分析每个script
    for i, script in enumerate(scripts):
        script_text = script.string or ''
        
        if not script_text:
            continue
        
        print(f"\\nScript #{i}:")
        print(f"  长度: {len(script_text)}")
        
        # 查找关键词
        keywords = ['__INITIAL_STATE__', 'videoData', 'aweme', 'videoInfo', 'window.__']
        found_keywords = [kw for kw in keywords if kw in script_text]
        
        if found_keywords:
            print(f"  关键词: {found_keywords}")
            
            # 保存有价值的script
            if any(kw in script_text for kw in ['__INITIAL_STATE__', 'videoData', 'aweme']):
                filename = f'/tmp/douyin_script_{i}.js'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(script_text)
                print(f"  已保存到 {filename}")
                
                # 尝试解析JSON
                try:
                    # 尝试不同的模式
                    patterns = [
                        r'window\\.__INITIAL_STATE__\\s*=\\s*(\\{.*?\\});',
                        r'__INITIAL_STATE__\\s*=\\s*(\\{.*?\\});',
                        r'(\\{[^{}]*"[^"]*"aweme"[^"]*":[^}]*\\})',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script_text, re.DOTALL)
                        if matches:
                            print(f"  找到 {len(matches)} 个匹配（模式: {pattern[:30]}...）")
                            
                            for j, match in enumerate(matches[:3]):  # 只显示前3个
                                try:
                                    data = json.loads(match)
                                    print(f"  JSON #{j}: {list(data.keys())[:10]}")
                                except:
                                    pass
                except Exception as e:
                    pass
    
    # 查找meta标签
    print("\\n\\n分析meta标签:")
    meta_tags = soup.find_all('meta')
    
    interesting_meta = ['og:title', 'og:description', 'og:video', 'og:image']
    
    for meta in meta_tags:
        prop = meta.get('property') or meta.get('name')
        if prop and any(interest in prop for interest in interesting_meta):
            content = meta.get('content', '')
            print(f"  {prop}: {content[:100]}")


if __name__ == "__main__":
    url = "https://v.douyin.com/arLquTQPBYM/"
    print("="*60)
    print("抖音页面分析")
    print("="*60)
    print(f"URL: {url}\\n")
    
    analyze_douyin_page(url)
    
    print("\\n" + "="*60)
    print("分析完成！")
    print("="*60)
    print("\\n文件已保存到 /tmp/")
    print("可以手动分析这些文件以了解数据结构")
