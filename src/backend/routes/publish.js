const express = require('express');
const router = express.Router();
const publishScheduler = require('../services/publish/scheduler');
const analyticsService = require('../services/publish/analytics');
const logger = require('../utils/logger');

router.post('/schedule', async (req, res, next) => {
  try {
    const { contentId, platformId, platformAccountId, scheduledTime, timezone, metadata } = req.body;

    const task = await publishScheduler.schedulePublish({
      contentId,
      platformId,
      platformAccountId,
      scheduledTime,
      timezone,
      metadata
    });

    res.status(201).json({
      success: true,
      data: task,
      message: 'Publish task scheduled successfully'
    });
  } catch (error) {
    next(error);
  }
});

router.get('/tasks', async (req, res, next) => {
  try {
    const { page, limit, status, platformId, orderBy, orderDir } = req.query;

    const result = await publishScheduler.listTasks({
      page: parseInt(page) || 1,
      limit: parseInt(limit) || 20,
      status,
      platformId: platformId ? parseInt(platformId) : undefined,
      orderBy,
      orderDir
    });

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.get('/tasks/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const task = await publishScheduler.getTask(id);

    if (!task) {
      return res.status(404).json({
        success: false,
        error: 'Task not found'
      });
    }

    res.json({
      success: true,
      data: task
    });
  } catch (error) {
    next(error);
  }
});

router.put('/tasks/:id/cancel', async (req, res, next) => {
  try {
    const { id } = req.params;
    const task = await publishScheduler.cancelSchedule(id);

    if (!task) {
      return res.status(404).json({
        success: false,
        error: 'Task not found or cannot be cancelled'
      });
    }

    res.json({
      success: true,
      data: task,
      message: 'Task cancelled successfully'
    });
  } catch (error) {
    next(error);
  }
});

router.post('/tasks/:id/retry', async (req, res, next) => {
  try {
    const { id } = req.params;
    const task = await publishScheduler.retryTask(id);

    res.json({
      success: true,
      data: task,
      message: 'Task scheduled for retry'
    });
  } catch (error) {
    next(error);
  }
});

router.get('/platforms', (req, res) => {
  const platforms = [
    { id: 1, code: 'xiaohongshu', name: '小红书', enabled: true },
    { id: 2, code: 'bilibili', name: '哔哩哔哩', enabled: true },
    { id: 3, code: 'weibo', name: '微博', enabled: false },
    { id: 4, code: 'zhihu', name: '知乎', enabled: false }
  ];

  res.json({
    success: true,
    data: platforms
  });
});

router.get('/scheduler/status', (req, res) => {
  const stats = publishScheduler.getStats();

  res.json({
    success: true,
    data: stats
  });
});

router.post('/scheduler/start', (req, res) => {
  publishScheduler.start();

  res.json({
    success: true,
    message: 'Scheduler started'
  });
});

router.post('/scheduler/stop', (req, res) => {
  publishScheduler.stop();

  res.json({
    success: true,
    message: 'Scheduler stopped'
  });
});

router.get('/analytics/overview', async (req, res, next) => {
  try {
    const { startDate, endDate } = req.query;
    const stats = await analyticsService.getOverallStats({ startDate, endDate });

    res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    next(error);
  }
});

router.get('/analytics/content/:contentId', async (req, res, next) => {
  try {
    const { contentId } = req.params;
    const analytics = await analyticsService.getContentAnalytics(contentId);

    res.json({
      success: true,
      data: analytics
    });
  } catch (error) {
    next(error);
  }
});

router.get('/analytics/platform/:platformId', async (req, res, next) => {
  try {
    const { platformId } = req.params;
    const { startDate, endDate, groupBy } = req.query;

    const analytics = await analyticsService.getPlatformAnalytics(
      parseInt(platformId),
      { startDate, endDate, groupBy }
    );

    res.json({
      success: true,
      data: analytics
    });
  } catch (error) {
    next(error);
  }
});

router.get('/analytics/top-content', async (req, res, next) => {
  try {
    const { limit, metric } = req.query;
    const content = await analyticsService.getTopContent(
      parseInt(limit) || 10,
      metric || 'views'
    );

    res.json({
      success: true,
      data: content
    });
  } catch (error) {
    next(error);
  }
});

router.get('/analytics/trend', async (req, res, next) => {
  try {
    const { days } = req.query;
    const trend = await analyticsService.getPublishTrend(parseInt(days) || 30);

    res.json({
      success: true,
      data: trend
    });
  } catch (error) {
    next(error);
  }
});

router.get('/analytics/engagement/:taskId', async (req, res, next) => {
  try {
    const { taskId } = req.params;
    const engagement = await analyticsService.getEngagementRate(taskId);

    if (!engagement) {
      return res.status(404).json({
        success: false,
        error: 'Analytics not found'
      });
    }

    res.json({
      success: true,
      data: engagement
    });
  } catch (error) {
    next(error);
  }
});

router.get('/report', async (req, res, next) => {
  try {
    const { platformId, startDate, endDate, reportType } = req.query;
    const report = await analyticsService.generateReport({
      platformId: platformId ? parseInt(platformId) : undefined,
      startDate,
      endDate,
      reportType
    });

    res.json({
      success: true,
      data: report
    });
  } catch (error) {
    next(error);
  }
});

router.post('/preview', async (req, res, next) => {
  try {
    const { content, platform } = req.body;

    if (!content || !platform) {
      return res.status(400).json({
        success: false,
        error: 'content and platform are required'
      });
    }

    const preview = {
      platform,
      title: content.title || 'Untitled',
      contentPreview: content.content ? content.content.substring(0, 200) + '...' : '',
      estimatedReach: '1K-5K',
      bestTimeToPost: '19:00-21:00',
      recommendations: [
        '建议添加封面图片',
        '标题可以更吸引眼球',
        '建议添加相关话题标签'
      ]
    };

    res.json({
      success: true,
      data: preview
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
