const OpenAI = require('openai');
const { redis } = require('../config');
const logger = require('../utils/logger');

class AIService {
  constructor() {
    this.openai = null;
    this.model = process.env.OPENAI_MODEL || 'gpt-4';
    this.maxTokens = parseInt(process.env.OPENAI_MAX_TOKENS) || 2000;
    this.initialized = false;
  }

  initialize() {
    if (this.initialized) return;
    
    const apiKey = process.env.OPENAI_API_KEY;
    if (apiKey && apiKey !== 'your-openai-api-key') {
      this.openai = new OpenAI({ apiKey });
      this.initialized = true;
      logger.info('OpenAI service initialized');
    } else {
      logger.warn('OpenAI API key not configured, using fallback mode');
    }
  }

  async generateCompletion(prompt, options = {}) {
    this.initialize();

    const cacheKey = `ai:completion:${Buffer.from(prompt).toString('base64').substring(0, 50)}`;
    const cached = await redis.get(cacheKey);
    if (cached) {
      return cached;
    }

    if (this.openai) {
      try {
        const response = await this.openai.chat.completions.create({
          model: options.model || this.model,
          messages: [
            { role: 'system', content: options.systemPrompt || '你是一个专业的内容创作助手。' },
            { role: 'user', content: prompt }
          ],
          max_tokens: options.maxTokens || this.maxTokens,
          temperature: options.temperature || 0.7
        });

        const result = response.choices[0].message.content;
        await redis.set(cacheKey, result, 3600);
        return result;
      } catch (error) {
        logger.error('OpenAI API error:', error);
        throw error;
      }
    }

    return this.fallbackCompletion(prompt, options);
  }

  fallbackCompletion(prompt, options = {}) {
    logger.debug('Using fallback completion mode');
    
    if (prompt.includes('标题') || prompt.includes('标题优化')) {
      return this.generateFallbackTitles(prompt);
    }
    if (prompt.includes('标签') || prompt.includes('话题')) {
      return this.generateFallbackTags(prompt);
    }
    if (prompt.includes('小红书') || prompt.includes('笔记')) {
      return this.generateFallbackXiaohongshuContent(prompt);
    }
    
    return 'AI服务暂未配置，请设置OPENAI_API_KEY环境变量。';
  }

  generateFallbackTitles(prompt) {
    const titleTemplates = [
      '🔥 {topic}必看！超详细攻略分享',
      '【{topic}】小白也能轻松上手！',
      '💡 关于{topic}，你必须知道的几件事',
      '✨ {topic}干货满满，建议收藏！',
      '🌟 {topic}经验分享，少走弯路！',
      '📝 {topic}完整指南，一篇搞定！',
      '🎯 {topic}避坑指南，亲测有效！',
      '💪 {topic}进阶技巧，高手必备！'
    ];
    
    const topicMatch = prompt.match(/主题[：:]\s*([^\n，。！？]+)/);
    const topic = topicMatch ? topicMatch[1].trim() : '这个话题';
    
    const titles = titleTemplates
      .map(template => template.replace('{topic}', topic))
      .slice(0, 5);
    
    return JSON.stringify({ titles });
  }

  generateFallbackTags(prompt) {
    const tagCategories = {
      '生活': ['生活记录', '日常分享', '生活小技巧', '好物推荐', '生活灵感'],
      '美食': ['美食分享', '食谱', '探店', '美食推荐', '吃货日常'],
      '旅行': ['旅行攻略', '旅游推荐', '打卡圣地', '旅行日记', '出行指南'],
      '美妆': ['美妆教程', '护肤心得', '化妆品推荐', '妆容分享', '变美技巧'],
      '穿搭': ['穿搭灵感', '时尚搭配', 'OOTD', '穿搭分享', '时尚穿搭'],
      '健身': ['健身打卡', '运动日常', '减肥经验', '健身教程', '身材管理'],
      '学习': ['学习笔记', '知识分享', '干货整理', '学习方法', '自我提升'],
      '职场': ['职场经验', '工作心得', '面试技巧', '职业发展', '职场干货']
    };
    
    for (const [category, tags] of Object.entries(tagCategories)) {
      if (prompt.includes(category)) {
        return JSON.stringify({ tags: tags.slice(0, 5) });
      }
    }
    
    return JSON.stringify({ tags: ['生活分享', '日常记录', '好物推荐', '干货分享', '经验总结'] });
  }

  generateFallbackXiaohongshuContent(prompt) {
    return `【标题】✨ 干货分享 | 超实用技巧推荐

【正文】
姐妹们好呀～今天来分享一个超实用的内容！

📌 首先，我们要明确目标
好的开始是成功的一半，规划很重要！

💡 其次，掌握核心技巧
这些方法亲测有效，建议收藏！

✨ 最后，持续优化改进
坚持就是胜利，一起加油！

【标签】
#干货分享 #实用技巧 #经验总结 #生活记录

【小贴士】
记得点赞收藏哦～有问题欢迎评论区留言！`;
  }

  async generateXiaohongshuContent(topic, style = '干货分享') {
    const prompt = `请为小红书创作一篇关于"${topic}"的笔记内容。
风格：${style}
要求：
1. 标题要吸引眼球，使用emoji
2. 正文结构清晰，分段明确
3. 语气亲切，像朋友聊天
4. 适当使用emoji增加趣味性
5. 结尾要有互动引导
6. 推荐5-8个相关话题标签

请以JSON格式返回：
{
  "title": "标题",
  "content": "正文内容",
  "tags": ["标签1", "标签2", ...]
}`;

    try {
      const result = await this.generateCompletion(prompt, {
        systemPrompt: '你是一个专业的小红书内容创作者，擅长写出爆款笔记。'
      });
      
      try {
        return JSON.parse(result);
      } catch {
        return {
          title: `✨ ${topic}干货分享`,
          content: result,
          tags: ['干货分享', topic, '经验总结']
        };
      }
    } catch (error) {
      logger.error('Failed to generate Xiaohongshu content:', error);
      return null;
    }
  }

  async optimizeTitle(originalTitle, platform = 'xiaohongshu') {
    const platformPrompts = {
      xiaohongshu: '小红书标题要吸引眼球、使用emoji、制造好奇心',
      bilibili: 'B站标题要有信息量、突出亮点、吸引点击',
      weibo: '微博标题要简洁有力、引发共鸣、便于传播'
    };

    const prompt = `请优化以下${platform === 'xiaohongshu' ? '小红书' : platform === 'bilibili' ? 'B站' : '微博'}标题：

原标题：${originalTitle}

要求：
1. ${platformPrompts[platform] || '吸引眼球'}
2. 保持原意，提升吸引力
3. 长度适中（15-25字）
4. 提供5个优化版本

请以JSON格式返回：
{
  "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
  "analysis": "优化说明"
}`;

    try {
      const result = await this.generateCompletion(prompt, {
        systemPrompt: '你是一个专业的标题优化专家，擅长写出吸引人的标题。'
      });
      
      try {
        return JSON.parse(result);
      } catch {
        return {
          titles: [
            `🔥 ${originalTitle}`,
            `✨ ${originalTitle}必看！`,
            `💡 关于${originalTitle}，你必须知道`,
            `🌟 ${originalTitle}干货分享`,
            `📝 ${originalTitle}完整指南`
          ],
          analysis: '基于原标题进行优化，增加emoji和吸引力'
        };
      }
    } catch (error) {
      logger.error('Failed to optimize title:', error);
      return null;
    }
  }

  async suggestTags(content, platform = 'xiaohongshu') {
    const prompt = `请为以下内容推荐合适的话题标签（平台：${platform}）：

内容：${content.substring(0, 500)}

要求：
1. 推荐8-12个标签
2. 包含热门标签和精准标签
3. 标签要有搜索价值
4. 按相关性排序

请以JSON格式返回：
{
  "tags": [
    {"tag": "标签名", "type": "hot/precise", "relevance": 0.95}
  ]
}`;

    try {
      const result = await this.generateCompletion(prompt, {
        systemPrompt: '你是一个社交媒体运营专家，擅长话题标签优化。'
      });
      
      try {
        return JSON.parse(result);
      } catch {
        return {
          tags: [
            { tag: '干货分享', type: 'hot', relevance: 0.9 },
            { tag: '经验总结', type: 'hot', relevance: 0.85 },
            { tag: '生活记录', type: 'hot', relevance: 0.8 },
            { tag: '实用技巧', type: 'precise', relevance: 0.95 }
          ]
        };
      }
    } catch (error) {
      logger.error('Failed to suggest tags:', error);
      return null;
    }
  }

  async improveContent(content, improvements = []) {
    const improvementMap = {
      'readability': '提高可读性，增加段落划分',
      'engagement': '增加互动引导，提升参与度',
      'emoji': '适当添加emoji，增加趣味性',
      'structure': '优化内容结构，增加小标题',
      'tone': '调整语气，更加亲切自然'
    };

    const improvementList = improvements.map(i => improvementMap[i] || i).join('、');

    const prompt = `请优化以下内容：

原文：
${content}

优化方向：${improvementList || '整体优化'}

要求：
1. 保持原文核心信息
2. 按指定方向优化
3. 提升内容质量
4. 保持原文风格

请返回优化后的完整内容。`;

    try {
      const result = await this.generateCompletion(prompt, {
        systemPrompt: '你是一个专业的内容编辑，擅长优化各类文案。'
      });
      
      return result;
    } catch (error) {
      logger.error('Failed to improve content:', error);
      return null;
    }
  }

  async suggestPublishTime(platform = 'xiaohongshu') {
    const timeSlots = {
      xiaohongshu: [
        { time: '07:00-09:00', description: '早高峰，通勤时间', score: 0.85 },
        { time: '12:00-14:00', description: '午休时间', score: 0.90 },
        { time: '18:00-20:00', description: '晚高峰，下班时间', score: 0.95 },
        { time: '21:00-23:00', description: '睡前刷手机高峰', score: 0.92 }
      ],
      bilibili: [
        { time: '12:00-14:00', description: '午休时间', score: 0.85 },
        { time: '18:00-22:00', description: '晚间黄金时段', score: 0.95 },
        { time: '22:00-24:00', description: '深夜活跃时段', score: 0.88 }
      ],
      weibo: [
        { time: '08:00-10:00', description: '早间新闻时段', score: 0.90 },
        { time: '12:00-14:00', description: '午间休息', score: 0.85 },
        { time: '20:00-22:00', description: '晚间活跃时段', score: 0.92 }
      ]
    };

    return timeSlots[platform] || timeSlots.xiaohongshu;
  }

  async analyzeContentPerformance(content) {
    const prompt = `请分析以下内容的潜在表现：

内容：
${content.substring(0, 500)}

请从以下维度分析：
1. 标题吸引力（0-100分）
2. 内容质量（0-100分）
3. 情感共鸣度（0-100分）
4. 传播潜力（0-100分）
5. 互动预期（0-100分）

请以JSON格式返回：
{
  "scores": {
    "titleAppeal": 85,
    "contentQuality": 80,
    "emotionalResonance": 75,
    "spreadPotential": 82,
    "interactionExpectation": 78
  },
  "overallScore": 80,
  "suggestions": ["建议1", "建议2", "建议3"]
}`;

    try {
      const result = await this.generateCompletion(prompt, {
        systemPrompt: '你是一个数据分析专家，擅长预测内容表现。'
      });
      
      try {
        return JSON.parse(result);
      } catch {
        return {
          scores: {
            titleAppeal: 75,
            contentQuality: 80,
            emotionalResonance: 70,
            spreadPotential: 72,
            interactionExpectation: 68
          },
          overallScore: 73,
          suggestions: [
            '标题可以更加吸引眼球',
            '增加互动引导元素',
            '适当使用emoji增加趣味性'
          ]
        };
      }
    } catch (error) {
      logger.error('Failed to analyze content performance:', error);
      return null;
    }
  }
}

module.exports = new AIService();
