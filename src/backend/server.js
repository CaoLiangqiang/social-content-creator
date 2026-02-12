const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
require('dotenv').config();

const logger = require('./utils/logger');
const { errorHandler } = require('./middleware/errorHandler');
const { rateLimiter } = require('./middleware/rateLimiter');
const { performanceMiddleware, requestLogger, errorTracker } = require('./middleware/performance');
const { initializeDatabase, closeAll, healthCheck } = require('./config');

const healthRoutes = require('./routes/health');
const userRoutes = require('./routes/users');
const contentRoutes = require('./routes/contents');
const crawlerRoutes = require('./routes/crawler');
const analysisRoutes = require('./routes/analysis');
const publishRoutes = require('./routes/publish');
const aiRoutes = require('./routes/ai');
const debugRoutes = require('./routes/debug');
const testRoutes = require('./routes/test');

const app = express();

const isProduction = process.env.NODE_ENV === 'production';

app.use(helmet({
  contentSecurityPolicy: isProduction,
  crossOriginEmbedderPolicy: isProduction
}));

app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  credentials: true
}));

app.use(compression());

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

app.use(requestLogger);
app.use(performanceMiddleware);

const API_PREFIX = process.env.API_PREFIX || '/api/v1';

app.use(`${API_PREFIX}/health`, healthRoutes);
app.use(`${API_PREFIX}/users`, userRoutes);
app.use(`${API_PREFIX}/contents`, contentRoutes);
app.use(`${API_PREFIX}/crawler`, crawlerRoutes);
app.use(`${API_PREFIX}/analysis`, analysisRoutes);
app.use(`${API_PREFIX}/publish`, publishRoutes);
app.use(`${API_PREFIX}/ai`, aiRoutes);
app.use(`${API_PREFIX}/debug`, debugRoutes);
app.use(`${API_PREFIX}/test`, testRoutes);

app.get('/', (req, res) => {
  const endpoints = {
    health: `${API_PREFIX}/health`,
    users: `${API_PREFIX}/users`,
    contents: `${API_PREFIX}/contents`,
    crawler: `${API_PREFIX}/crawler`,
    analysis: `${API_PREFIX}/analysis`,
    publish: `${API_PREFIX}/publish`,
    ai: `${API_PREFIX}/ai`
  };
  
  if (!isProduction) {
    endpoints.debug = `${API_PREFIX}/debug`;
    endpoints.test = `${API_PREFIX}/test`;
  }
  
  res.json({
    name: 'Social Content Creator Platform',
    version: '0.4.0',
    status: 'running',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    endpoints
  });
});

app.get(`${API_PREFIX}/db-health`, async (req, res) => {
  try {
    const health = await healthCheck();
    res.json({
      success: true,
      data: health
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`
  });
});

app.use(errorTracker);
app.use(errorHandler);

const PORT = process.env.PORT || 3000;

async function startServer() {
  try {
    logger.info('Initializing database connections...');
    const dbResults = await initializeDatabase();
    
    const dbStatus = Object.entries(dbResults)
      .map(([name, connected]) => `${name}: ${connected ? 'connected' : 'failed'}`)
      .join(', ');
    logger.info(`Database status: ${dbStatus}`);

    const server = app.listen(PORT, () => {
      logger.info(`🚀 Server is running on port ${PORT}`);
      logger.info(`📝 Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`🌐 API Base URL: http://localhost:${PORT}${API_PREFIX}`);
      logger.info(`📊 Log Level: ${logger.logLevel}`);
      logger.info(`🔧 Debug Mode: ${logger.debugMode ? 'enabled' : 'disabled'}`);
      
      const hasOpenAI = process.env.OPENAI_API_KEY && 
                        process.env.OPENAI_API_KEY !== 'your-openai-api-key';
      logger.info(`🤖 AI Service: ${hasOpenAI ? 'OpenAI configured' : 'Fallback mode'}`);
      
      if (!isProduction) {
        logger.info(`🔍 Debug endpoints: ${API_PREFIX}/debug/*`);
        logger.info(`🧪 Test endpoints: ${API_PREFIX}/test/*`);
      }
    });

    const gracefulShutdown = async (signal) => {
      logger.info(`Received ${signal}. Closing server gracefully...`);
      
      server.close(async () => {
        logger.info('Server closed, closing database connections...');
        logger.flush();
        await closeAll();
        logger.info('All connections closed successfully');
        process.exit(0);
      });

      setTimeout(async () => {
        logger.error('Forced shutdown after timeout');
        logger.flush();
        await closeAll();
        process.exit(1);
      }, 10000);
    };

    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

    process.on('uncaughtException', async (error) => {
      logger.error('Uncaught Exception:', error);
      logger.flush();
      await closeAll();
      process.exit(1);
    });

    process.on('unhandledRejection', async (reason, promise) => {
      logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    return server;
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

module.exports = app;
