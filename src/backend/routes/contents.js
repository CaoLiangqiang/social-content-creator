const express = require('express');
const router = express.Router();
const { Content, AnalysisResult } = require('../models');
const { redis } = require('../config');
const logger = require('../utils/logger');

router.get('/', async (req, res, next) => {
  try {
    const {
      page = 1,
      limit = 20,
      platformId,
      contentType,
      status,
      authorId,
      search,
      orderBy,
      orderDir
    } = req.query;

    const result = await Content.list({
      page: parseInt(page),
      limit: parseInt(limit),
      platformId: platformId ? parseInt(platformId) : undefined,
      contentType,
      status,
      authorId,
      search,
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

router.get('/hot', async (req, res, next) => {
  try {
    const { platformId, limit = 10 } = req.query;

    if (!platformId) {
      return res.status(400).json({
        success: false,
        error: 'platformId is required'
      });
    }

    const cacheKey = `hot:content:${platformId}`;
    const cached = await redis.get(cacheKey);
    
    if (cached) {
      return res.json({
        success: true,
        data: cached,
        cached: true
      });
    }

    const contents = await Content.getHotContents(parseInt(platformId), parseInt(limit));
    
    await redis.set(cacheKey, contents, 300);

    res.json({
      success: true,
      data: contents
    });
  } catch (error) {
    next(error);
  }
});

router.get('/trending-tags', async (req, res, next) => {
  try {
    const { platformId, limit = 20 } = req.query;

    if (!platformId) {
      return res.status(400).json({
        success: false,
        error: 'platformId is required'
      });
    }

    const tags = await Content.getTrendingTags(parseInt(platformId), parseInt(limit));

    res.json({
      success: true,
      data: tags
    });
  } catch (error) {
    next(error);
  }
});

router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    
    const cacheKey = `content:${id}`;
    const cached = await redis.get(cacheKey);
    
    if (cached) {
      return res.json({
        success: true,
        data: cached,
        cached: true
      });
    }

    const content = await Content.findById(id);

    if (!content) {
      return res.status(404).json({
        success: false,
        error: 'Content not found'
      });
    }

    await Content.incrementViewCount(id);
    
    await redis.set(cacheKey, content, 3600);

    res.json({
      success: true,
      data: content
    });
  } catch (error) {
    next(error);
  }
});

router.post('/', async (req, res, next) => {
  try {
    const contentData = req.body;

    const content = await Content.create(contentData);

    res.status(201).json({
      success: true,
      data: content,
      message: 'Content created successfully'
    });
  } catch (error) {
    next(error);
  }
});

router.put('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const updates = req.body;

    const content = await Content.update(id, updates);

    if (!content) {
      return res.status(404).json({
        success: false,
        error: 'Content not found'
      });
    }

    await redis.del(`content:${id}`);

    res.json({
      success: true,
      data: content,
      message: 'Content updated successfully'
    });
  } catch (error) {
    next(error);
  }
});

router.delete('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;

    await Content.delete(id);
    
    await redis.del(`content:${id}`);

    res.json({
      success: true,
      message: 'Content deleted successfully'
    });
  } catch (error) {
    next(error);
  }
});

router.get('/:id/analysis', async (req, res, next) => {
  try {
    const { id } = req.params;

    const analysis = await AnalysisResult.findByContentId(id);

    if (!analysis) {
      return res.status(404).json({
        success: false,
        error: 'Analysis not found for this content'
      });
    }

    res.json({
      success: true,
      data: analysis
    });
  } catch (error) {
    next(error);
  }
});

router.get('/:id/snapshots', async (req, res, next) => {
  try {
    const { id } = req.params;
    const { days = 7 } = req.query;

    const { ContentSnapshot } = require('../models/mongo');
    const snapshots = await ContentSnapshot.getSnapshotHistory(id, parseInt(days));

    res.json({
      success: true,
      data: snapshots
    });
  } catch (error) {
    next(error);
  }
});

router.post('/batch', async (req, res, next) => {
  try {
    const { contents } = req.body;

    if (!Array.isArray(contents) || contents.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'contents must be a non-empty array'
      });
    }

    const results = [];
    for (const contentData of contents) {
      try {
        const content = await Content.create(contentData);
        results.push({ success: true, data: content });
      } catch (error) {
        results.push({ success: false, error: error.message });
      }
    }

    res.status(201).json({
      success: true,
      data: results,
      message: `Processed ${results.length} contents`
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
