const express = require('express');
const router = express.Router();
const os = require('os');
const v8 = require('v8');
const logger = require('../utils/logger');
const { healthCheck } = require('../config');
const {
  getPerformanceStats,
  getRecentRequests,
  getSlowQueries,
  getRecentErrors,
  clearMetrics
} = require('../middleware/performance');

const DEBUG_SECRET = process.env.DEBUG_SECRET;
const isProduction = process.env.NODE_ENV === 'production';

function debugAuth(req, res, next) {
  if (isProduction) {
    const secret = req.headers['x-debug-secret'] || req.query.secret;
    if (!DEBUG_SECRET || secret !== DEBUG_SECRET) {
      return res.status(403).json({
        success: false,
        error: 'Debug access denied in production'
      });
    }
  }
  next();
}

router.get('/status', debugAuth, async (req, res) => {
  try {
    const dbHealth = await healthCheck();
    const perfStats = getPerformanceStats();
    const loggerStats = logger.getStats();
    
    const memoryUsage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();
    const heapStats = v8.getHeapStatistics();
    
    res.json({
      success: true,
      data: {
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'development',
        nodeVersion: process.version,
        platform: process.platform,
        uptime: perfStats.uptimeFormatted,
        uptimeSeconds: perfStats.uptime,
        
        memory: {
          rss: formatBytes(memoryUsage.rss),
          heapTotal: formatBytes(memoryUsage.heapTotal),
          heapUsed: formatBytes(memoryUsage.heapUsed),
          external: formatBytes(memoryUsage.external),
          arrayBuffers: formatBytes(memoryUsage.arrayBuffers)
        },
        
        heap: {
          totalHeapSize: formatBytes(heapStats.total_heap_size),
          totalHeapSizeExecutable: formatBytes(heapStats.total_heap_size_executable),
          totalPhysicalSize: formatBytes(heapStats.total_physical_size),
          totalAvailableSize: formatBytes(heapStats.total_available_size),
          usedHeapSize: formatBytes(heapStats.used_heap_size),
          heapSizeLimit: formatBytes(heapStats.heap_size_limit),
          mallocedMemory: formatBytes(heapStats.malloced_memory),
          peakMallocedMemory: formatBytes(heapStats.peak_malloced_memory)
        },
        
        cpu: {
          user: cpuUsage.user,
          system: cpuUsage.system
        },
        
        system: {
          cpus: os.cpus().length,
          totalMemory: formatBytes(os.totalmem()),
          freeMemory: formatBytes(os.freemem()),
          loadAverage: os.loadavg()
        },
        
        database: dbHealth,
        
        performance: perfStats,
        
        logging: loggerStats
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/performance', debugAuth, (req, res) => {
  const stats = getPerformanceStats();
  
  res.json({
    success: true,
    data: stats
  });
});

router.get('/requests', debugAuth, (req, res) => {
  const { limit = 50, slow, errors } = req.query;
  
  let requests;
  if (slow === 'true') {
    requests = getSlowQueries(parseInt(limit));
  } else if (errors === 'true') {
    requests = getRecentErrors(parseInt(limit));
  } else {
    requests = getRecentRequests(parseInt(limit));
  }
  
  res.json({
    success: true,
    data: {
      count: requests.length,
      requests
    }
  });
});

router.get('/logs', debugAuth, (req, res) => {
  const { level, limit = 100 } = req.query;
  
  res.json({
    success: true,
    data: {
      message: 'Log streaming not implemented. Check log files.',
      logFiles: [
        'combined.log',
        'error.log',
        'request.log',
        'performance.log',
        'audit.log'
      ],
      logLevel: logger.logLevel,
      debugMode: logger.debugMode
    }
  });
});

router.post('/log-level', debugAuth, (req, res) => {
  const { level } = req.body;
  
  if (!level) {
    return res.status(400).json({
      success: false,
      error: 'Log level is required'
    });
  }
  
  try {
    logger.setLogLevel(level);
    res.json({
      success: true,
      message: `Log level set to ${level}`,
      data: logger.getStats()
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/debug-mode', debugAuth, (req, res) => {
  const { enabled } = req.body;
  
  if (enabled) {
    logger.enableDebugMode();
  } else {
    logger.disableDebugMode();
  }
  
  res.json({
    success: true,
    message: `Debug mode ${enabled ? 'enabled' : 'disabled'}`,
    data: logger.getStats()
  });
});

router.post('/clear-metrics', debugAuth, (req, res) => {
  clearMetrics();
  
  res.json({
    success: true,
    message: 'Performance metrics cleared'
  });
});

router.get('/env', debugAuth, (req, res) => {
  const safeEnv = {
    NODE_ENV: process.env.NODE_ENV,
    PORT: process.env.PORT,
    API_PREFIX: process.env.API_PREFIX,
    LOG_LEVEL: process.env.LOG_LEVEL,
    DEBUG_MODE: process.env.DEBUG_MODE,
    PG_HOST: process.env.PG_HOST ? '***' : undefined,
    PG_PORT: process.env.PG_PORT,
    PG_DATABASE: process.env.PG_DATABASE,
    PG_USER: process.env.PG_USER,
    PG_POOL_MAX: process.env.PG_POOL_MAX,
    MONGO_POOL_SIZE: process.env.MONGO_POOL_SIZE,
    REDIS_HOST: process.env.REDIS_HOST,
    REDIS_PORT: process.env.REDIS_PORT,
    REDIS_DB: process.env.REDIS_DB,
    JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN,
    CORS_ORIGIN: process.env.CORS_ORIGIN
  };
  
  res.json({
    success: true,
    data: safeEnv
  });
});

router.get('/routes', debugAuth, (req, res) => {
  const app = req.app;
  const routes = [];
  
  function extractRoutes(stack, basePath = '') {
    stack.forEach(layer => {
      if (layer.route) {
        const methods = Object.keys(layer.route.methods).map(m => m.toUpperCase());
        routes.push({
          path: basePath + layer.route.path,
          methods
        });
      } else if (layer.name === 'router' && layer.handle.stack) {
        const routerPath = layer.regexp.source
          .replace(/\\\//g, '/')
          .replace(/\?/g, '')
          .replace(/\(\?:\(\[\^\/\]\+\?\)\)/g, '*');
        extractRoutes(layer.handle.stack, basePath + routerPath);
      }
    });
  }
  
  try {
    extractRoutes(app._router.stack);
    res.json({
      success: true,
      data: {
        count: routes.length,
        routes
      }
    });
  } catch (error) {
    res.json({
      success: true,
      data: {
        message: 'Could not extract routes',
        error: error.message
      }
    });
  }
});

router.get('/health/detailed', debugAuth, async (req, res) => {
  const checks = {
    timestamp: new Date().toISOString(),
    checks: {}
  };
  
  checks.checks.memory = {
    status: process.memoryUsage().heapUsed < 500 * 1024 * 1024 ? 'ok' : 'warning',
    heapUsed: formatBytes(process.memoryUsage().heapUsed)
  };
  
  try {
    const dbHealth = await healthCheck();
    checks.checks.database = {
      status: dbHealth.status === 'healthy' ? 'ok' : 'degraded',
      details: dbHealth.services
    };
  } catch (error) {
    checks.checks.database = {
      status: 'error',
      error: error.message
    };
  }
  
  const perfStats = getPerformanceStats();
  checks.checks.performance = {
    status: perfStats.avgResponseTime < 500 ? 'ok' : 'warning',
    avgResponseTime: `${perfStats.avgResponseTime}ms`,
    requestsLastHour: perfStats.requestsLastHour
  };
  
  const allOk = Object.values(checks.checks).every(c => c.status === 'ok');
  checks.overall = allOk ? 'healthy' : 'degraded';
  
  res.json({
    success: true,
    data: checks
  });
});

router.post('/test/error', debugAuth, (req, res) => {
  const { type = 'generic' } = req.body;
  
  switch (type) {
    case 'generic':
      throw new Error('Test error triggered');
    case 'async':
      return Promise.reject(new Error('Async test error'));
    case 'timeout':
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(res.json({ success: true, message: 'Timeout test completed' }));
        }, 5000);
      });
    default:
      throw new Error(`Unknown test error type: ${type}`);
  }
});

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

module.exports = router;
