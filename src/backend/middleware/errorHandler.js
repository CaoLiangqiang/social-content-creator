const logger = require('../utils/logger');

/**
 * 错误处理中间件
 */
class AppError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;
    
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * 全局错误处理中间件
 */
const errorHandler = (err, req, res, next) => {
  let error = { ...err };
  error.message = err.message;

  // 记录错误日志
  logger.error('Error:', {
    message: err.message,
    stack: err.stack,
    statusCode: err.statusCode,
    path: req.path,
    method: req.method
  });

  // Mongoose验证错误
  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new AppError(message, 400);
  }

  // Mongoose重复键错误
  if (err.code === 11000) {
    const message = 'Resource already exists';
    error = new AppError(message, 400);
  }

  // Mongoose CastError（无效的ID）
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new AppError(message, 404);
  }

  // JWT错误
  if (err.name === 'JsonWebTokenError') {
    const message = 'Invalid token';
    error = new AppError(message, 401);
  }

  if (err.name === 'TokenExpiredError') {
    const message = 'Token expired';
    error = new AppError(message, 401);
  }

  // 返回错误响应
  res.status(error.statusCode || 500).json({
    success: false,
    error: {
      message: error.message || 'Internal Server Error',
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    }
  });
};

module.exports = { errorHandler, AppError };
