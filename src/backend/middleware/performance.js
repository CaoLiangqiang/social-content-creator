const logger = require('../utils/logger');
const { redis } = require('../config');

const performanceMetrics = {
  requests: [],
  slowQueries: [],
  errors: [],
  startTime: Date.now()
};

const MAX_METRICS_SIZE = 1000;

function performanceMiddleware(req, res, next) {
  const startTime = process.hrtime.bigint();
  const startTimestamp = Date.now();
  
  res.on('finish', () => {
    const endTime = process.hrtime.bigint();
    const durationNs = Number(endTime - startTime);
    const durationMs = durationNs / 1000000;
    
    const metric = {
      method: req.method,
      url: req.originalUrl || req.url,
      statusCode: res.statusCode,
      durationMs: Math.round(durationMs * 100) / 100,
      timestamp: startTimestamp,
      ip: req.ip,
      userAgent: req.get('user-agent'),
      userId: req.user?.id
    };
    
    performanceMetrics.requests.push(metric);
    
    if (performanceMetrics.requests.length > MAX_METRICS_SIZE) {
      performanceMetrics.requests.shift();
    }
    
    if (durationMs > 1000) {
      performanceMetrics.slowQueries.push({
        ...metric,
        durationMs: Math.round(durationMs * 100) / 100
      });
      
      if (performanceMetrics.slowQueries.length > 100) {
        performanceMetrics.slowQueries.shift();
      }
      
      logger.warn('Slow request detected', {
        method: req.method,
        url: req.originalUrl,
        duration: `${(durationMs).toFixed(2)}ms`
      });
    }
    
    if (res.statusCode >= 400) {
      performanceMetrics.errors.push({
        ...metric,
        durationMs: Math.round(durationMs * 100) / 100
      });
      
      if (performanceMetrics.errors.length > 100) {
        performanceMetrics.errors.shift();
      }
    }
    
    logger.logRequest(req, res, Math.round(durationMs * 100) / 100);
  });
  
  next();
}

function requestLogger(req, res, next) {
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  req.requestId = requestId;
  req.startTime = Date.now();
  
  logger.http(`--> ${req.method} ${req.originalUrl || req.url}`, {
    requestId,
    ip: req.ip,
    query: Object.keys(req.query).length > 0 ? req.query : undefined,
    body: req.method !== 'GET' && Object.keys(req.body || {}).length > 0 ? 
      JSON.stringify(req.body).substring(0, 500) : undefined
  });
  
  const originalEnd = res.end;
  res.end = function(chunk, encoding) {
    const duration = Date.now() - req.startTime;
    
    logger.http(`<-- ${req.method} ${req.originalUrl || req.url}`, {
      requestId,
      statusCode: res.statusCode,
      duration: `${duration}ms`
    });
    
    originalEnd.call(this, chunk, encoding);
  };
  
  next();
}

function errorTracker(err, req, res, next) {
  const errorInfo = {
    requestId: req.requestId,
    method: req.method,
    url: req.originalUrl || req.url,
    error: {
      message: err.message,
      stack: err.stack,
      name: err.name
    },
    timestamp: new Date().toISOString(),
    userId: req.user?.id
  };
  
  performanceMetrics.errors.push({
    method: req.method,
    url: req.originalUrl || req.url,
    statusCode: res.statusCode || 500,
    timestamp: Date.now(),
    error: err.message
  });
  
  logger.error('Request error', errorInfo);
  
  next(err);
}

function getPerformanceStats() {
  const now = Date.now();
  const uptime = now - performanceMetrics.startTime;
  
  const requestsLastHour = performanceMetrics.requests.filter(
    r => r.timestamp > now - 3600000
  );
  
  const avgResponseTime = requestsLastHour.length > 0
    ? requestsLastHour.reduce((sum, r) => sum + r.durationMs, 0) / requestsLastHour.length
    : 0;
  
  const statusCodes = {};
  requestsLastHour.forEach(r => {
    const code = Math.floor(r.statusCode / 100) * 100;
    statusCodes[code] = (statusCodes[code] || 0) + 1;
  });
  
  return {
    uptime: Math.floor(uptime / 1000),
    uptimeFormatted: formatUptime(uptime),
    totalRequests: performanceMetrics.requests.length,
    requestsLastHour: requestsLastHour.length,
    avgResponseTime: Math.round(avgResponseTime * 100) / 100,
    slowQueries: performanceMetrics.slowQueries.length,
    errors: performanceMetrics.errors.length,
    statusCodes,
    requestsPerMinute: requestsLastHour.length / 60
  };
}

function getRecentRequests(limit = 50) {
  return performanceMetrics.requests.slice(-limit);
}

function getSlowQueries(limit = 20) {
  return performanceMetrics.slowQueries.slice(-limit);
}

function getRecentErrors(limit = 20) {
  return performanceMetrics.errors.slice(-limit);
}

function formatUptime(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}d ${hours % 24}h ${minutes % 60}m`;
  if (hours > 0) return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

function clearMetrics() {
  performanceMetrics.requests = [];
  performanceMetrics.slowQueries = [];
  performanceMetrics.errors = [];
  logger.info('Performance metrics cleared');
}

module.exports = {
  performanceMiddleware,
  requestLogger,
  errorTracker,
  getPerformanceStats,
  getRecentRequests,
  getSlowQueries,
  getRecentErrors,
  clearMetrics,
  performanceMetrics
};
