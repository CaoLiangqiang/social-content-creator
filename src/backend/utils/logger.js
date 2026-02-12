const winston = require('winston');
const path = require('path');
const fs = require('fs');

const LOG_LEVELS = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  verbose: 4,
  debug: 5,
  silly: 6
};

const LOG_COLORS = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  verbose: 'cyan',
  debug: 'blue',
  silly: 'gray'
};

winston.addColors(LOG_COLORS);

class LoggerService {
  constructor() {
    this.loggers = new Map();
    this.performanceMetrics = new Map();
    this.debugMode = process.env.DEBUG_MODE === 'true';
    this.logLevel = process.env.LOG_LEVEL || 'info';
    this.isProduction = process.env.NODE_ENV === 'production';
    
    this.logsDir = path.join(__dirname, '../../logs');
    this._ensureLogsDir();
    
    this.defaultLogger = this._createLogger('default');
    
    this.requestLogger = this._createLogger('request', {
      filename: 'request.log'
    });
    
    this.performanceLogger = this._createLogger('performance', {
      filename: 'performance.log',
      level: 'debug'
    });
    
    this.auditLogger = this._createLogger('audit', {
      filename: 'audit.log'
    });
  }
  
  _ensureLogsDir() {
    if (!fs.existsSync(this.logsDir)) {
      fs.mkdirSync(this.logsDir, { recursive: true });
    }
  }
  
  _createLogger(name, options = {}) {
    const logLevel = options.level || this.logLevel;
    const filename = options.filename || `${name}.log`;
    
    const customFormat = winston.format.combine(
      winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
      winston.format.errors({ stack: true }),
      winston.format.splat(),
      winston.format.json()
    );
    
    const consoleFormat = winston.format.combine(
      winston.format.colorize({ all: true }),
      winston.format.timestamp({ format: 'HH:mm:ss.SSS' }),
      winston.format.printf(({ level, message, timestamp, module, ...metadata }) => {
        const moduleStr = module ? `[${module}]` : '';
        const metaStr = Object.keys(metadata).length > 0 ? ` ${JSON.stringify(metadata)}` : '';
        return `${timestamp} ${moduleStr} [${level}]: ${message}${metaStr}`;
      })
    );
    
    const transports = [
      new winston.transports.Console({
        format: consoleFormat,
        level: this.isProduction ? 'info' : logLevel,
        silent: options.silentConsole !== true ? false : this.isProduction
      })
    ];
    
    if (!this.isProduction || options.persistInProduction) {
      transports.push(
        new winston.transports.File({
          filename: path.join(this.logsDir, filename),
          format: customFormat,
          maxsize: options.maxsize || 10485760,
          maxFiles: options.maxFiles || 5,
          level: logLevel
        })
      );
    }
    
    if (name === 'default' || name === 'error') {
      transports.push(
        new winston.transports.File({
          filename: path.join(this.logsDir, 'error.log'),
          level: 'error',
          format: customFormat,
          maxsize: 10485760,
          maxFiles: 10
        })
      );
    }
    
    const logger = winston.createLogger({
      level: logLevel,
      levels: LOG_LEVELS,
      transports,
      exitOnError: false
    });
    
    this.loggers.set(name, logger);
    return logger;
  }
  
  getLogger(name) {
    if (!this.loggers.has(name)) {
      return this._createLogger(name);
    }
    return this.loggers.get(name);
  }
  
  setLogLevel(level) {
    if (!LOG_LEVELS.hasOwnProperty(level)) {
      throw new Error(`Invalid log level: ${level}`);
    }
    this.logLevel = level;
    this.loggers.forEach(logger => {
      logger.transports.forEach(transport => {
        if (transport.level) {
          transport.level = level;
        }
      });
    });
  }
  
  enableDebugMode() {
    this.debugMode = true;
    this.setLogLevel('debug');
  }
  
  disableDebugMode() {
    this.debugMode = false;
    this.setLogLevel(this.isProduction ? 'info' : 'info');
  }
  
  _log(level, message, meta = {}) {
    const logger = meta.logger ? this.getLogger(meta.logger) : this.defaultLogger;
    const logMeta = { ...meta };
    delete logMeta.logger;
    logger.log(level, message, logMeta);
  }
  
  error(message, meta = {}) {
    this._log('error', message, meta);
  }
  
  warn(message, meta = {}) {
    this._log('warn', message, meta);
  }
  
  info(message, meta = {}) {
    this._log('info', message, meta);
  }
  
  http(message, meta = {}) {
    this._log('http', message, meta);
  }
  
  verbose(message, meta = {}) {
    this._log('verbose', message, meta);
  }
  
  debug(message, meta = {}) {
    if (this.debugMode || !this.isProduction) {
      this._log('debug', message, meta);
    }
  }
  
  silly(message, meta = {}) {
    this._log('silly', message, meta);
  }
  
  logRequest(req, res, responseTime) {
    const logData = {
      method: req.method,
      url: req.originalUrl || req.url,
      statusCode: res.statusCode,
      responseTime: `${responseTime}ms`,
      ip: req.ip || req.connection.remoteAddress,
      userAgent: req.get('user-agent'),
      userId: req.user?.id
    };
    
    this.requestLogger.http(`${req.method} ${req.originalUrl || req.url}`, logData);
  }
  
  startTimer(operationName, meta = {}) {
    const startTime = process.hrtime.bigint();
    const timerId = `${operationName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.performanceMetrics.set(timerId, {
      operationName,
      startTime,
      meta,
      startTimestamp: Date.now()
    });
    
    return timerId;
  }
  
  endTimer(timerId, additionalMeta = {}) {
    const metric = this.performanceMetrics.get(timerId);
    if (!metric) {
      this.warn(`Timer not found: ${timerId}`);
      return null;
    }
    
    const endTime = process.hrtime.bigint();
    const durationNs = Number(endTime - metric.startTime);
    const durationMs = durationNs / 1000000;
    
    this.performanceMetrics.delete(timerId);
    
    const logData = {
      operation: metric.operationName,
      duration: `${durationMs.toFixed(2)}ms`,
      durationNs,
      ...metric.meta,
      ...additionalMeta
    };
    
    this.performanceLogger.debug(`PERF: ${metric.operationName}`, logData);
    
    if (durationMs > 1000) {
      this.warn(`Slow operation: ${metric.operationName}`, { duration: `${durationMs.toFixed(2)}ms` });
    }
    
    return {
      operationName: metric.operationName,
      durationMs,
      durationNs
    };
  }
  
  audit(action, details = {}) {
    this.auditLogger.info(`AUDIT: ${action}`, {
      action,
      timestamp: new Date().toISOString(),
      ...details
    });
  }
  
  logError(error, context = {}) {
    const errorInfo = {
      message: error.message,
      stack: error.stack,
      name: error.name,
      ...context
    };
    
    this.error(error.message, errorInfo);
  }
  
  logModule(moduleName, level, message, meta = {}) {
    this._log(level, message, { module: moduleName, ...meta });
  }
  
  createModuleLogger(moduleName) {
    return {
      error: (message, meta = {}) => this.logModule(moduleName, 'error', message, meta),
      warn: (message, meta = {}) => this.logModule(moduleName, 'warn', message, meta),
      info: (message, meta = {}) => this.logModule(moduleName, 'info', message, meta),
      http: (message, meta = {}) => this.logModule(moduleName, 'http', message, meta),
      verbose: (message, meta = {}) => this.logModule(moduleName, 'verbose', message, meta),
      debug: (message, meta = {}) => this.logModule(moduleName, 'debug', message, meta),
      silly: (message, meta = {}) => this.logModule(moduleName, 'silly', message, meta),
      startTimer: (operationName, meta = {}) => this.startTimer(`${moduleName}:${operationName}`, meta),
      endTimer: (timerId, meta = {}) => this.endTimer(timerId, meta)
    };
  }
  
  getStats() {
    return {
      logLevel: this.logLevel,
      debugMode: this.debugMode,
      isProduction: this.isProduction,
      activeTimers: this.performanceMetrics.size,
      registeredLoggers: Array.from(this.loggers.keys())
    };
  }
  
  flush() {
    this.loggers.forEach(logger => {
      logger.transports.forEach(transport => {
        if (typeof transport.flush === 'function') {
          transport.flush();
        }
      });
    });
  }
}

const loggerService = new LoggerService();

module.exports = loggerService;
module.exports.LoggerService = LoggerService;
module.exports.LOG_LEVELS = LOG_LEVELS;
