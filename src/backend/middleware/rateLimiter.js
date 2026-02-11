const rateLimit = require('express-rate-limit');
const logger = require('../utils/logger');

/**
 * 通用API速率限制
 */
const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100, // 限制100个请求
  message: {
    success: false,
    error: 'Too many requests, please try again later'
  },
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    logger.warn('Rate limit exceeded', {
      ip: req.ip,
      path: req.path
    });
    res.status(429).json({
      success: false,
      error: 'Too many requests, please try again later'
    });
  }
});

/**
 * 爬虫API速率限制（更严格）
 */
const crawlerRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1分钟
  max: 10, // 限制10个请求
  message: {
    success: false,
    error: 'Crawler rate limit exceeded'
  }
});

module.exports = { rateLimiter, crawlerRateLimiter };
