const pg = require('./database');
const mongo = require('./mongodb');
const redis = require('./redis');
const logger = require('../utils/logger');

async function initializeDatabase() {
  logger.info('Initializing database connections...');
  
  const results = {
    postgresql: false,
    mongodb: false,
    redis: false
  };

  try {
    results.postgresql = await pg.testConnection();
  } catch (error) {
    logger.error('PostgreSQL initialization failed', error);
  }

  try {
    results.mongodb = await mongo.testConnection();
  } catch (error) {
    logger.error('MongoDB initialization failed', error);
  }

  try {
    results.redis = await redis.testConnection();
  } catch (error) {
    logger.error('Redis initialization failed', error);
  }

  const allConnected = results.postgresql && results.mongodb && results.redis;
  
  logger.info('Database initialization complete', {
    postgresql: results.postgresql ? 'connected' : 'failed',
    mongodb: results.mongodb ? 'connected' : 'failed',
    redis: results.redis ? 'connected' : 'failed',
    overall: allConnected ? 'success' : 'partial'
  });

  return results;
}

async function closeAll() {
  logger.info('Closing all database connections...');
  
  try {
    await pg.close();
  } catch (error) {
    logger.error('Error closing PostgreSQL', error);
  }

  try {
    await mongo.disconnect();
  } catch (error) {
    logger.error('Error closing MongoDB', error);
  }

  try {
    await redis.close();
  } catch (error) {
    logger.error('Error closing Redis', error);
  }

  logger.info('All database connections closed');
}

async function healthCheck() {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {}
  };

  try {
    await pg.query('SELECT 1');
    health.services.postgresql = { status: 'up' };
  } catch (error) {
    health.services.postgresql = { status: 'down', error: error.message };
    health.status = 'degraded';
  }

  try {
    if (mongo.isConnectedToMongo()) {
      health.services.mongodb = { status: 'up' };
    } else {
      throw new Error('Not connected');
    }
  } catch (error) {
    health.services.mongodb = { status: 'down', error: error.message };
    health.status = 'degraded';
  }

  try {
    if (redis.isReady()) {
      health.services.redis = { status: 'up' };
    } else {
      throw new Error('Not connected');
    }
  } catch (error) {
    health.services.redis = { status: 'down', error: error.message };
    health.status = 'degraded';
  }

  return health;
}

module.exports = {
  pg,
  mongo,
  redis,
  initializeDatabase,
  closeAll,
  healthCheck
};
