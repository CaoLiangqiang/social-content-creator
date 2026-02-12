const express = require('express');
const router = express.Router();
const aiService = require('../services/ai');
const { redis } = require('../config');
const logger = require('../utils/logger');

router.post('/generate/xiaohongshu', async (req, res, next) => {
  try {
    const { topic, style = '干货分享' } = req.body;

    if (!topic) {
      return res.status(400).json({
        success: false,
        error: 'Topic is required'
      });
    }

    const cacheKey = `ai:xiaohongshu:${topic}:${style}`;
    const cached = await redis.get(cacheKey);
    
    if (cached) {
      return res.json({
        success: true,
        data: cached,
        cached: true
      });
    }

    const result = await aiService.generateXiaohongshuContent(topic, style);

    if (result) {
      await redis.set(cacheKey, result, 1800);
    }

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.post('/optimize/title', async (req, res, next) => {
  try {
    const { title, platform = 'xiaohongshu' } = req.body;

    if (!title) {
      return res.status(400).json({
        success: false,
        error: 'Title is required'
      });
    }

    const result = await aiService.optimizeTitle(title, platform);

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.post('/suggest/tags', async (req, res, next) => {
  try {
    const { content, platform = 'xiaohongshu' } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const result = await aiService.suggestTags(content, platform);

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.post('/improve/content', async (req, res, next) => {
  try {
    const { content, improvements = [] } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const result = await aiService.improveContent(content, improvements);

    res.json({
      success: true,
      data: {
        original: content,
        improved: result
      }
    });
  } catch (error) {
    next(error);
  }
});

router.get('/suggest/publish-time', async (req, res, next) => {
  try {
    const { platform = 'xiaohongshu' } = req.query;

    const result = await aiService.suggestPublishTime(platform);

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.post('/analyze/performance', async (req, res, next) => {
  try {
    const { content } = req.body;

    if (!content) {
      return res.status(400).json({
        success: false,
        error: 'Content is required'
      });
    }

    const result = await aiService.analyzeContentPerformance(content);

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.post('/complete', async (req, res, next) => {
  try {
    const { prompt, systemPrompt, temperature, maxTokens } = req.body;

    if (!prompt) {
      return res.status(400).json({
        success: false,
        error: 'Prompt is required'
      });
    }

    const result = await aiService.generateCompletion(prompt, {
      systemPrompt,
      temperature,
      maxTokens
    });

    res.json({
      success: true,
      data: {
        prompt: prompt.substring(0, 100) + (prompt.length > 100 ? '...' : ''),
        result
      }
    });
  } catch (error) {
    next(error);
  }
});

router.get('/status', (req, res) => {
  const hasOpenAI = process.env.OPENAI_API_KEY && 
                    process.env.OPENAI_API_KEY !== 'your-openai-api-key';

  res.json({
    success: true,
    data: {
      openaiConfigured: hasOpenAI,
      model: process.env.OPENAI_MODEL || 'gpt-4',
      maxTokens: parseInt(process.env.OPENAI_MAX_TOKENS) || 2000,
      fallbackMode: !hasOpenAI
    }
  });
});

router.post('/batch', async (req, res, next) => {
  try {
    const { tasks } = req.body;

    if (!Array.isArray(tasks) || tasks.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Tasks must be a non-empty array'
      });
    }

    const results = [];
    
    for (const task of tasks) {
      try {
        let result;
        
        switch (task.type) {
          case 'generate':
            result = await aiService.generateXiaohongshuContent(task.topic, task.style);
            break;
          case 'optimizeTitle':
            result = await aiService.optimizeTitle(task.title, task.platform);
            break;
          case 'suggestTags':
            result = await aiService.suggestTags(task.content, task.platform);
            break;
          case 'improve':
            result = await aiService.improveContent(task.content, task.improvements);
            break;
          default:
            result = { error: 'Unknown task type' };
        }
        
        results.push({ success: true, data: result });
      } catch (error) {
        results.push({ success: false, error: error.message });
      }
    }

    res.json({
      success: true,
      data: results,
      message: `Processed ${results.length} tasks`
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
