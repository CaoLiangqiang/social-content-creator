"""
AI内容生成服务
基于FastAPI框架，提供内容生成、改写、分析等功能
"""

import os
import re
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

# 配置
app = FastAPI(
    title="SCCP AI Service",
    description="AI内容生成服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI配置
openai.api_key = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
FALLBACK_MODE = not openai.api_key or openai.api_key == "your-openai-api-key"


# 数据模型
class XiaohongshuGenerateRequest(BaseModel):
    """小红书内容生成请求"""
    topic: str = Field(..., min_length=1, max_length=200, description="内容主题")
    style: str = Field(default="干货分享", description="内容风格")
    keywords: List[str] = Field(default=[], max_length=10, description="关键词")
    tone: str = Field(default="轻松", description="语气")
    length: str = Field(default="medium", description="长度")


class TitleOptimizeRequest(BaseModel):
    """标题优化请求"""
    title: str = Field(..., min_length=1, max_length=100, description="原标题")
    platform: str = Field(default="xiaohongshu", description="目标平台")
    count: int = Field(default=3, ge=1, le=10, description="生成数量")


class ContentImproveRequest(BaseModel):
    """内容改进请求"""
    content: str = Field(..., min_length=10, max_length=5000, description="原始内容")
    improvement_type: str = Field(default="general", description="改进类型")


class AnalysisRequest(BaseModel):
    """内容分析请求"""
    content: str = Field(..., min_length=10, max_length=5000, description="内容")


class GenerateResponse(BaseModel):
    """生成响应"""
    success: bool
    data: Dict
    message: str = "success"


# Prompt模板
XIAOHONGSHU_PROMPT = """你是一个专业的小红书内容创作者。请根据以下信息创作一篇小红书笔记：

主题：{topic}
风格：{style}
语气：{tone}
长度：{length}
关键词：{keywords}

要求：
1. 标题要吸引人，使用emoji，控制在20字以内
2. 正文要有干货，结构清晰，使用emoji点缀
3. 开头要有吸引力，能留住读者
4. 中间要有实用内容，提供价值
5. 结尾要有互动，引导评论点赞
6. 添加相关话题标签，5-10个
7. 使用小红书风格，亲切自然

请按以下格式输出：
标题：[标题内容]
正文：[正文内容]
标签：[标签列表]
"""

TITLE_OPTIMIZE_PROMPT = """你是一个专业的标题优化专家。请为以下标题优化{count}个版本：

原标题：{title}
目标平台：{platform}

要求：
1. 吸引人点击
2. 符合平台调性
3. 使用emoji增加吸引力
4. 控制在20字以内
5. 每个版本要有不同角度

请直接输出优化后的标题列表，每行一个。
"""

CONTENT_IMPROVE_PROMPT = """你是一个专业的内容编辑。请改进以下内容：

原始内容：
{content}

改进类型：{improvement_type}

要求：
1. 保持原意
2. 优化表达方式
3. 增加可读性
4. 修正语法错误
5. 使内容更流畅

请输出改进后的内容。
"""


# 工具函数
def parse_xiaohongshu_content(text: str) -> Dict:
    """解析小红书生成内容"""
    result = {
        "title": "",
        "content": "",
        "tags": []
    }
    
    # 解析标题
    title_match = re.search(r'标题[:：]\s*(.+?)(?=\n|$)', text)
    if title_match:
        result["title"] = title_match.group(1).strip()
    
    # 解析正文
    content_match = re.search(r'正文[:：]\s*([\s\S]+?)(?=标签[:：]|$)', text)
    if content_match:
        result["content"] = content_match.group(1).strip()
    
    # 解析标签
    tags_match = re.search(r'标签[:：]\s*(.+?)(?=\n|$)', text)
    if tags_match:
        tags_text = tags_match.group(1)
        # 提取标签（支持 #标签 或 标签 格式）
        tags = re.findall(r'#?([^#\s,]+)', tags_text)
        result["tags"] = [tag.strip() for tag in tags if tag.strip()]
    
    return result


def get_length_instruction(length: str) -> str:
    """获取长度说明"""
    lengths = {
        "short": "简短精炼，100-200字",
        "medium": "中等长度，300-500字",
        "long": "详细全面，800-1000字"
    }
    return lengths.get(length, lengths["medium"])


# OpenAI调用
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
async def call_openai(prompt: str, model: str = None) -> str:
    """调用OpenAI API"""
    if FALLBACK_MODE:
        raise Exception("OpenAI API not configured")
    
    model = model or DEFAULT_MODEL
    
    response = await openai.ChatCompletion.acreate(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个专业的内容创作助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content


# Fallback生成器
class FallbackGenerator:
    """当OpenAI不可用时使用的Fallback生成器"""
    
    @staticmethod
    def generate_xiaohongshu(topic: str, style: str, keywords: List[str]) -> Dict:
        """生成小红书内容（Fallback）"""
        keyword_str = " ".join([f"#{k}" for k in keywords[:5]]) if keywords else "#干货分享"
        
        title_templates = [
            f"✨{topic}超全攻略！建议收藏",
            f"🔥{topic}必看！新手也能学会",
            f"💡{topic}的秘密，90%的人都不知道",
            f"📌{topic}干货｜亲测有效",
            f"🌟{topic}这样做，效果翻倍"
        ]
        
        title = title_templates[hash(topic) % len(title_templates)]
        
        content = f"""姐妹们！今天来分享{topic}的超实用经验💕

【为什么重要】
{topic}真的太重要了！做好{topic}可以让我们的生活/工作更加高效✨

【核心要点】
1️⃣ 首先要明确目标，知道自己想要什么
2️⃣ 制定详细的计划，分步骤执行
3️⃣ 坚持执行，不要轻易放弃
4️⃣ 及时复盘总结，不断优化改进

【实用技巧】
💡 技巧一：从小事做起，循序渐进
💡 技巧二：找到适合自己的方法
💡 技巧三：多向优秀的人学习

【注意事项】
⚠️ 不要盲目跟风，要根据自己的实际情况
⚠️ 保持耐心，不要急于求成
⚠️ 定期回顾，及时调整方向

希望这些分享对大家有帮助！如果觉得有用记得点赞收藏哦～
有问题欢迎在评论区留言交流💬

{keyword_str} #干货分享 #经验分享 #生活技巧"""
        
        tags = keywords + ["干货分享", "经验分享", "生活技巧", "实用攻略"]
        
        return {
            "title": title,
            "content": content,
            "tags": tags[:10]
        }
    
    @staticmethod
    def optimize_title(title: str, count: int = 3) -> List[str]:
        """优化标题（Fallback）"""
        return [
            f"✨{title}｜超全攻略",
            f"🔥{title}必看！建议收藏",
            f"💡{title}的秘密"
        ][:count]
    
    @staticmethod
    def improve_content(content: str) -> str:
        """改进内容（Fallback）"""
        return f"【优化版】\n\n{content}\n\n💡 小贴士：建议结合实际情况灵活运用以上内容。"


# API端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ai-service",
        "fallback_mode": FALLBACK_MODE,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/generate/xiaohongshu", response_model=GenerateResponse)
async def generate_xiaohongshu(request: XiaohongshuGenerateRequest):
    """生成小红书内容"""
    try:
        if not FALLBACK_MODE:
            # 使用OpenAI生成
            prompt = XIAOHONGSHU_PROMPT.format(
                topic=request.topic,
                style=request.style,
                tone=request.tone,
                length=get_length_instruction(request.length),
                keywords=", ".join(request.keywords) if request.keywords else "无"
            )
            
            result_text = await call_openai(prompt)
            result = parse_xiaohongshu_content(result_text)
        else:
            # 使用Fallback生成
            result = FallbackGenerator.generate_xiaohongshu(
                request.topic,
                request.style,
                request.keywords
            )
        
        return GenerateResponse(
            success=True,
            data={
                "title": result["title"],
                "content": result["content"],
                "tags": result["tags"],
                "generated_at": datetime.now().isoformat(),
                "model": "fallback" if FALLBACK_MODE else DEFAULT_MODEL,
                "fallback_mode": FALLBACK_MODE
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize/title", response_model=GenerateResponse)
async def optimize_title(request: TitleOptimizeRequest):
    """优化标题"""
    try:
        if not FALLBACK_MODE:
            prompt = TITLE_OPTIMIZE_PROMPT.format(
                title=request.title,
                platform=request.platform,
                count=request.count
            )
            
            result_text = await call_openai(prompt)
            titles = [line.strip() for line in result_text.split('\n') if line.strip()]
        else:
            titles = FallbackGenerator.optimize_title(request.title, request.count)
        
        return GenerateResponse(
            success=True,
            data={
                "original_title": request.title,
                "optimized_titles": titles[:request.count],
                "generated_at": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/improve/content", response_model=GenerateResponse)
async def improve_content(request: ContentImproveRequest):
    """改进内容"""
    try:
        if not FALLBACK_MODE:
            prompt = CONTENT_IMPROVE_PROMPT.format(
                content=request.content,
                improvement_type=request.improvement_type
            )
            
            improved_content = await call_openai(prompt)
        else:
            improved_content = FallbackGenerator.improve_content(request.content)
        
        return GenerateResponse(
            success=True,
            data={
                "original_content": request.content,
                "improved_content": improved_content,
                "improvement_type": request.improvement_type,
                "generated_at": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/sentiment", response_model=GenerateResponse)
async def analyze_sentiment(request: AnalysisRequest):
    """情感分析"""
    # 简单的情感分析实现
    positive_words = ['好', '棒', '优秀', '喜欢', '推荐', '赞', '完美', '满意']
    negative_words = ['差', '坏', '糟糕', '失望', '讨厌', '烂', '垃圾', '后悔']
    
    content = request.content
    positive_count = sum(1 for word in positive_words if word in content)
    negative_count = sum(1 for word in negative_words if word in content)
    
    total = positive_count + negative_count
    if total == 0:
        sentiment = "neutral"
        score = 0.5
    else:
        score = positive_count / total
        if score > 0.6:
            sentiment = "positive"
        elif score < 0.4:
            sentiment = "negative"
        else:
            sentiment = "neutral"
    
    return GenerateResponse(
        success=True,
        data={
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "analyzed_at": datetime.now().isoformat()
        }
    )


@app.post("/analyze/keywords", response_model=GenerateResponse)
async def extract_keywords(request: AnalysisRequest):
    """关键词提取"""
    # 简单的关键词提取实现
    import jieba
    
    words = jieba.lcut(request.content)
    # 过滤停用词和短词
    keywords = [w for w in words if len(w) >= 2 and w not in ['我们', '你们', '他们', '这个', '那个']]
    # 统计词频
    from collections import Counter
    keyword_counts = Counter(keywords)
    top_keywords = keyword_counts.most_common(10)
    
    return GenerateResponse(
        success=True,
        data={
            "keywords": [{"word": word, "count": count} for word, count in top_keywords],
            "total_words": len(words),
            "analyzed_at": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
