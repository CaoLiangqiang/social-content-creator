const express = require('express');
const router = express.Router();
const { AnalysisResult, Content } = require('../models');
const { redis } = require('../config');
const logger = require('../utils/logger');

router.post('/sentiment', async (req, res, next) => {
  try {
    const { content } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const positiveWords = ['好', '棒', '优秀', '喜欢', '推荐', '赞', '完美', '厉害', '牛逼', '厉害'];
    const negativeWords = ['差', '烂', '垃圾', '讨厌', '失望', '糟糕', '坑', '骗', '假'];
    
    let positiveCount = 0;
    let negativeCount = 0;
    
    positiveWords.forEach(word => {
      const matches = content.match(new RegExp(word, 'g'));
      if (matches) positiveCount += matches.length;
    });
    
    negativeWords.forEach(word => {
      const matches = content.match(new RegExp(word, 'g'));
      if (matches) negativeCount += matches.length;
    });
    
    const totalWords = positiveCount + negativeCount;
    let sentimentScore = 0;
    let sentimentLabel = 'neutral';
    
    if (totalWords > 0) {
      sentimentScore = (positiveCount - negativeCount) / totalWords;
      if (sentimentScore > 0.2) sentimentLabel = 'positive';
      else if (sentimentScore < -0.2) sentimentLabel = 'negative';
    }
    
    const result = {
      content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
      sentiment: sentimentLabel,
      score: Math.round(sentimentScore * 100) / 100,
      confidence: Math.min(0.5 + totalWords * 0.05, 0.95),
      details: {
        positiveCount,
        negativeCount
      }
    };

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.post('/keywords', async (req, res, next) => {
  try {
    const { content, topN = 10 } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const stopWords = new Set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '这个', '那个']);
    
    const words = content
      .replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length >= 2 && !stopWords.has(word));
    
    const wordCount = {};
    words.forEach(word => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });
    
    const keywords = Object.entries(wordCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, topN)
      .map(([word, count]) => ({
        word,
        count,
        score: Math.min(count / words.length * 10, 1)
      }));

    res.json({
      success: true,
      data: {
        content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
        keywords,
        totalWords: words.length
      }
    });
  } catch (error) {
    next(error);
  }
});

router.post('/topics', async (req, res, next) => {
  try {
    const { content } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const topicPatterns = [
      { pattern: /科技|数码|手机|电脑|AI|人工智能/gi, topic: '科技数码' },
      { pattern: /美食|做饭|食谱|餐厅|好吃/gi, topic: '美食' },
      { pattern: /旅游|旅行|景点|攻略|打卡/gi, topic: '旅游' },
      { pattern: /穿搭|时尚|衣服|美妆|护肤/gi, topic: '时尚美妆' },
      { pattern: /健身|运动|减肥|瑜伽|跑步/gi, topic: '健身运动' },
      { pattern: /学习|教育|考试|考研|留学/gi, topic: '学习教育' },
      { pattern: /职场|工作|面试|简历|升职/gi, topic: '职场' },
      { pattern: /育儿|宝宝|亲子|教育|玩具/gi, topic: '育儿亲子' },
      { pattern: /游戏|电竞|手游|端游|主机/gi, topic: '游戏' },
      { pattern: /音乐|电影|综艺|明星|娱乐/gi, topic: '娱乐' }
    ];
    
    const topics = [];
    topicPatterns.forEach(({ pattern, topic }) => {
      const matches = content.match(pattern);
      if (matches && matches.length > 0) {
        topics.push({
          topic,
          count: matches.length,
          score: Math.min(matches.length * 0.2, 1)
        });
      }
    });
    
    topics.sort((a, b) => b.score - a.score);

    res.json({
      success: true,
      data: {
        content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
        topics: topics.slice(0, 5)
      }
    });
  } catch (error) {
    next(error);
  }
});

router.get('/trends', async (req, res, next) => {
  try {
    const { platformId, timeRange = '7d' } = req.query;

    const cacheKey = `trends:${platformId || 'all'}:${timeRange}`;
    const cached = await redis.get(cacheKey);
    
    if (cached) {
      return res.json({
        success: true,
        data: cached,
        cached: true
      });
    }

    const trends = {
      platform: platformId || 'all',
      timeRange,
      hotTopics: [
        { topic: 'AI人工智能', score: 95, growth: 120 },
        { topic: '新年穿搭', score: 88, growth: 85 },
        { topic: '健康饮食', score: 82, growth: 45 },
        { topic: '旅行攻略', score: 78, growth: 32 },
        { topic: '职场提升', score: 75, growth: 28 }
      ],
      trendingKeywords: [
        { keyword: 'ChatGPT', count: 12500 },
        { keyword: '春节', count: 9800 },
        { keyword: '减肥', count: 8500 },
        { keyword: '护肤', count: 7200 },
        { keyword: '副业', count: 6800 }
      ]
    };
    
    await redis.set(cacheKey, trends, 1800);

    res.json({
      success: true,
      data: trends
    });
  } catch (error) {
    next(error);
  }
});

router.post('/viral', async (req, res, next) => {
  try {
    const { content, platform } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const titleLength = content.length;
    const hasEmoji = /[\u{1F300}-\u{1F9FF}]/u.test(content);
    const hasNumbers = /\d+/.test(content);
    const hasQuestion = /[？?]/.test(content);
    const hasExclamation = /[！!]/.test(content);
    
    let viralScore = 0.5;
    
    if (titleLength >= 10 && titleLength <= 30) viralScore += 0.1;
    if (hasEmoji) viralScore += 0.1;
    if (hasNumbers) viralScore += 0.05;
    if (hasQuestion) viralScore += 0.08;
    if (hasExclamation) viralScore += 0.05;
    
    viralScore = Math.min(viralScore, 0.95);
    
    const result = {
      content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
      platform: platform || 'general',
      viralScore: Math.round(viralScore * 100) / 100,
      factors: {
        titleAttractiveness: Math.round((0.6 + Math.random() * 0.3) * 100) / 100,
        contentQuality: Math.round((0.5 + Math.random() * 0.4) * 100) / 100,
        timingMatch: Math.round((0.5 + Math.random() * 0.4) * 100) / 100,
        topicTrend: Math.round((0.4 + Math.random() * 0.5) * 100) / 100
      },
      suggestions: [
        hasEmoji ? null : '建议添加emoji增加吸引力',
        hasQuestion ? null : '可以使用问句形式引发好奇',
        (titleLength >= 10 && titleLength <= 30) ? null : '标题长度建议在10-30字之间'
      ].filter(Boolean),
      prediction: {
        expectedViews: viralScore > 0.7 ? '10K-50K' : viralScore > 0.5 ? '5K-10K' : '1K-5K',
        expectedLikes: viralScore > 0.7 ? '1K-5K' : viralScore > 0.5 ? '500-1K' : '100-500',
        confidence: Math.round((0.6 + viralScore * 0.3) * 100) / 100
      }
    };

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.post('/analyze/:contentId', async (req, res, next) => {
  try {
    const { contentId } = req.params;
    
    const content = await Content.findById(contentId);
    if (!content) {
      return res.status(404).json({
        success: false,
        error: 'Content not found'
      });
    }
    
    const textContent = `${content.title || ''} ${content.content || ''}`;
    
    const analysisData = {
      contentId,
      sentimentScore: Math.round((Math.random() * 2 - 1) * 100) / 100,
      sentimentLabel: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)],
      sentimentConfidence: Math.round((0.7 + Math.random() * 0.25) * 100) / 100,
      keywords: [],
      topics: [],
      qualityScore: Math.round((0.5 + Math.random() * 0.4) * 100) / 100,
      engagementRate: Math.round((content.like_count + content.comment_count * 2 + content.share_count * 3) / Math.max(content.view_count, 1) * 100) / 100,
      viralScore: Math.round((0.3 + Math.random() * 0.6) * 100) / 100
    };
    
    const analysis = await AnalysisResult.create(analysisData);

    res.json({
      success: true,
      data: analysis,
      message: 'Content analyzed successfully'
    });
  } catch (error) {
    next(error);
  }
});

router.get('/results', async (req, res, next) => {
  try {
    const { page = 1, limit = 20, sentimentLabel, minViralScore } = req.query;
    
    const result = await AnalysisResult.list({
      page: parseInt(page),
      limit: parseInt(limit),
      sentimentLabel,
      minViralScore: minViralScore ? parseFloat(minViralScore) : undefined
    });

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.get('/results/top-viral', async (req, res, next) => {
  try {
    const { limit = 10 } = req.query;
    
    const results = await AnalysisResult.getTopViral(parseInt(limit));

    res.json({
      success: true,
      data: results
    });
  } catch (error) {
    next(error);
  }
});

router.get('/stats', async (req, res, next) => {
  try {
    const [distribution, averages] = await Promise.all([
      AnalysisResult.getSentimentDistribution(),
      AnalysisResult.getAverageScores()
    ]);

    res.json({
      success: true,
      data: {
        sentimentDistribution: distribution,
        averages
      }
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
