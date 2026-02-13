const redis = require('redis');
const logger = require('../utils/logger');

const client = redis.createClient({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD || undefined
});

client.on('error', (err) => {
  logger.error('Redis Client Error', err);
});

client.on('connect', () => {
  logger.info('Redis Client Connected');
});

const connectRedis = async () => {
  try {
    await client.connect();
  } catch (error) {
    logger.error('Failed to connect to Redis', error);
  }
};

const testConnection = async () => {
  try {
    await client.ping();
    return true;
  } catch (error) {
    logger.error('Redis connection test failed', error);
    return false;
  }
};

const isReady = () => {
  return client.isReady;
};

const close = async () => {
  await client.quit();
};

module.exports = {
  client,
  connectRedis,
  testConnection,
  isReady,
  close
};
