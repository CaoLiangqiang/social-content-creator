const express = require('express');
const router = express.Router();
const crawlerService = require('../services/crawler');
const { Content, CrawlerJob } = require('../models');
const logger = require('../utils/logger');

router.post('/start', async (req, res, next) => {
  try {
    const { platform, type = 'video', url, bvid, mid, keyword, noteId, limit = 20 } = req.body;

    let result;
    
    if (url) {
      result = await crawlerService.crawlByUrl(url);
    } else if (platform === 'bilibili') {
      if (type === 'video' && bvid) {
        result = await crawlerService.crawlBilibiliVideo(bvid);
      } else if (type === 'user' && mid) {
        result = await crawlerService.crawlBilibiliUser(mid);
      } else if (type === 'search' && keyword) {
        result = await crawlerService.searchBilibili(keyword, limit);
      } else {
        return res.status(400).json({
          success: false,
          error: 'Invalid parameters for Bilibili crawler'
        });
      }
    } else if (platform === 'douyin' && url) {
      result = await crawlerService.crawlDouyinVideo(url);
    } else if (platform === 'xiaohongshu' && noteId) {
      result = await crawlerService.crawlXiaohongshuNote(noteId);
    } else {
      return res.status(400).json({
        success: false,
        error: 'Invalid platform or missing required parameters'
      });
    }

    if (result.success && result.data) {
      try {
        await saveCrawledContent(platform, result.data);
      } catch (saveError) {
        logger.warn('Failed to save crawled content', saveError);
      }
    }

    res.json({
      success: result.success,
      data: result.data,
      error: result.error
    });
  } catch (error) {
    next(error);
  }
});

async function saveCrawledContent(platform, data) {
  if (!data || data.error) return;

  const platformMap = {
    'bilibili': 2,
    'douyin': 5,
    'xiaohongshu': 1
  };

  const platformId = platformMap[platform];
  if (!platformId) return;

  if (data.bvid || data.video_info) {
    const videoInfo = data.video_info || data;
    await Content.create({
      platformId,
      platformContentId: data.bvid || videoInfo.bvid,
      title: videoInfo.title,
      content: videoInfo.desc || videoInfo.description,
      contentType: 'video',
      authorId: videoInfo.author_id || videoInfo.mid,
      authorName: videoInfo.author || videoInfo.name,
      viewCount: videoInfo.view || videoInfo.play || 0,
      likeCount: videoInfo.like || 0,
      commentCount: videoInfo.comment || 0,
      url: `https://www.bilibili.com/video/${data.bvid}`,
      publishedAt: videoInfo.created ? new Date(videoInfo.created * 1000) : null
    });
  }
}

router.get('/jobs', async (req, res, next) => {
  try {
    const { page = 1, limit = 20, status, platformId } = req.query;
    
    const result = await CrawlerJob.list({
      page: parseInt(page),
      limit: parseInt(limit),
      status,
      platformId: platformId ? parseInt(platformId) : undefined
    });

    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

router.get('/jobs/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const job = await CrawlerJob.findById(id);

    if (!job) {
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }

    res.json({
      success: true,
      data: job
    });
  } catch (error) {
    next(error);
  }
});

router.put('/jobs/:id/cancel', async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const job = await CrawlerJob.cancel(id);
    
    crawlerService.cancelJob(id);

    res.json({
      success: true,
      data: job,
      message: 'Job cancelled successfully'
    });
  } catch (error) {
    next(error);
  }
});

router.get('/platforms', (req, res) => {
  const platforms = crawlerService.getSupportedPlatforms();

  res.json({
    success: true,
    data: platforms
  });
});

router.get('/stats', async (req, res, next) => {
  try {
    const stats = await CrawlerJob.getStats();
    
    res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    next(error);
  }
});

router.post('/url', async (req, res, next) => {
  try {
    const { url } = req.body;

    if (!url) {
      return res.status(400).json({
        success: false,
        error: 'URL is required'
      });
    }

    const result = await crawlerService.crawlByUrl(url);

    res.json({
      success: result.success,
      data: result.data,
      error: result.error
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
