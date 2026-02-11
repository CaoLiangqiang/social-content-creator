const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
require('dotenv').config();

const logger = require('./utils/logger');
const { errorHandler } = require('./middleware/errorHandler');
const { rateLimiter } = require('./middleware/rateLimiter');

// 路由导入
const healthRoutes = require('./routes/health');
const userRoutes = require('./routes/users');
const contentRoutes = require('./routes/contents');
const crawlerRoutes = require('./routes/crawler');
const analysisRoutes = require('./routes/analysis');
const publishRoutes = require('./routes/publish');

// 创建Express应用
const app = express();

// ============================================
// 中间件配置
// ============================================

// 安全头
app.use(helmet());

// CORS
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  credentials: true
}));

// 压缩
app.use(compression());

// JSON解析
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 请求日志
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('user-agent')
  });
  next();
});

// 速率限制
app.use('/api', rateLimiter);

// ============================================
// 路由配置
// ============================================

const API_PREFIX = process.env.API_PREFIX || '/api/v1';

// 健康检查
app.use(`${API_PREFIX}/health`, healthRoutes);

// API路由
app.use(`${API_PREFIX}/users`, userRoutes);
app.use(`${API_PREFIX}/contents`, contentRoutes);
app.use(`${API_PREFIX}/crawler`, crawlerRoutes);
app.use(`${API_PREFIX}/analysis`, analysisRoutes);
app.use(`${API_PREFIX}/publish`, publishRoutes);

// 根路径
app.get('/', (req, res) => {
  res.json({
    name: 'Social Content Creator Platform',
    version: '0.1.0',
    status: 'running',
    timestamp: new Date().toISOString()
  });
});

// 404处理
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`
  });
});

// 错误处理
app.use(errorHandler);

// ============================================
// 服务器启动
// ============================================

const PORT = process.env.PORT || 3000;

const server = app.listen(PORT, () => {
  logger.info(`🚀 Server is running on port ${PORT}`);
  logger.info(`📝 Environment: ${process.env.NODE_ENV || 'development'}`);
  logger.info(`🌐 API Base URL: http://localhost:${PORT}${API_PREFIX}`);
});

// 优雅关闭
const gracefulShutdown = (signal) => {
  logger.info(`Received ${signal}. Closing server gracefully...`);
  
  server.close(() => {
    logger.info('Server closed successfully');
    process.exit(0);
  });

  // 强制关闭超时
  setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// 未捕获的异常
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

module.exports = app;
