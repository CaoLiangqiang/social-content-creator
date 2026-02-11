const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

/**
 * @route   GET /api/v1/health
 * @desc    健康检查端点
 * @access  Public
 */
router.get('/', (req, res) => {
  const healthData = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
    version: '0.1.0'
  };

  res.json({
    success: true,
    data: healthData
  });
});

/**
 * @route   GET /api/v1/health/extended
 * @desc    扩展健康检查（数据库连接等）
 * @access  Public
 */
router.get('/extended', async (req, res) => {
  try {
    // TODO: 添加数据库连接检查
    // TODO: 添加Redis连接检查
    // TODO: 添加外部服务检查
    
    const healthData = {
      status: 'ok',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      environment: process.env.NODE_ENV || 'development',
      version: '0.1.0',
      services: {
        database: 'ok',
        redis: 'ok',
        elasticsearch: 'ok'
      }
    };

    res.json({
      success: true,
      data: healthData
    });
  } catch (error) {
    logger.error('Extended health check failed:', error);
    res.status(503).json({
      success: false,
      error: 'Service unavailable'
    });
  }
});

module.exports = router;
