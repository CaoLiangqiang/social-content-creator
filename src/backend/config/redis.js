const redis = require('redis');
const logger = require('../utils/logger');

const redisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD || undefined,
  db: parseInt(process.env.REDIS_DB || '0'),
  keyPrefix: process.env.REDIS_PREFIX || 'scc:',
};

let client = null;
let isConnected = false;

async function createClient() {
  if (client && isConnected) {
    return client;
  }

  client = redis.createClient({
    socket: {
      host: redisConfig.host,
      port: redisConfig.port,
      reconnectStrategy: (retries) => {
        if (retries > 10) {
          logger.error('Redis: Max reconnection attempts reached');
          return new Error('Max reconnection attempts reached');
        }
        const delay = Math.min(retries * 100, 3000);
        logger.warn(`Redis: Reconnecting in ${delay}ms (attempt ${retries})`);
        return delay;
      }
    },
    password: redisConfig.password,
    database: redisConfig.db,
  });

  client.on('connect', () => {
    logger.info('Redis: Connecting...');
  });

  client.on('ready', () => {
    logger.info('Redis: Connected and ready');
    isConnected = true;
  });

  client.on('error', (err) => {
    logger.error('Redis: Client error', err);
  });

  client.on('end', () => {
    logger.warn('Redis: Connection ended');
    isConnected = false;
  });

  client.on('disconnect', () => {
    logger.warn('Redis: Disconnected');
    isConnected = false;
  });

  await client.connect();
  return client;
}

async function getClient() {
  if (!client || !isConnected) {
    await createClient();
  }
  return client;
}

async function get(key) {
  const c = await getClient();
  const value = await c.get(key);
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return value;
  }
}

async function set(key, value, ttl = 3600) {
  const c = await getClient();
  const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
  await c.setEx(key, ttl, stringValue);
}

async function del(key) {
  const c = await getClient();
  await c.del(key);
}

async function exists(key) {
  const c = await getClient();
  return c.exists(key);
}

async function expire(key, ttl) {
  const c = await getClient();
  await c.expire(key, ttl);
}

async function ttl(key) {
  const c = await getClient();
  return c.ttl(key);
}

async function incr(key) {
  const c = await getClient();
  return c.incr(key);
}

async function decr(key) {
  const c = await getClient();
  return c.decr(key);
}

async function hSet(key, field, value) {
  const c = await getClient();
  const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
  await c.hSet(key, field, stringValue);
}

async function hGet(key, field) {
  const c = await getClient();
  const value = await c.hGet(key, field);
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return value;
  }
}

async function hGetAll(key) {
  const c = await getClient();
  const data = await c.hGetAll(key);
  const result = {};
  for (const [field, value] of Object.entries(data)) {
    try {
      result[field] = JSON.parse(value);
    } catch {
      result[field] = value;
    }
  }
  return result;
}

async function hDel(key, field) {
  const c = await getClient();
  await c.hDel(key, field);
}

async function zAdd(key, score, member) {
  const c = await getClient();
  await c.zAdd(key, { score, value: member });
}

async function zRange(key, start, stop, options = {}) {
  const c = await getClient();
  return c.zRange(key, start, stop, options);
}

async function zRangeByScore(key, min, max, options = {}) {
  const c = await getClient();
  return c.zRangeByScore(key, min, max, options);
}

async function zRem(key, member) {
  const c = await getClient();
  await c.zRem(key, member);
}

async function zScore(key, member) {
  const c = await getClient();
  return c.zScore(key, member);
}

async function lPush(key, value) {
  const c = await getClient();
  const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
  return c.lPush(key, stringValue);
}

async function rPush(key, value) {
  const c = await getClient();
  const stringValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
  return c.rPush(key, stringValue);
}

async function lPop(key) {
  const c = await getClient();
  const value = await c.lPop(key);
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return value;
  }
}

async function rPop(key) {
  const c = await getClient();
  const value = await c.rPop(key);
  try {
    return value ? JSON.parse(value) : null;
  } catch {
    return value;
  }
}

async function lRange(key, start, stop) {
  const c = await getClient();
  const values = await c.lRange(key, start, stop);
  return values.map(v => {
    try {
      return JSON.parse(v);
    } catch {
      return v;
    }
  });
}

async function testConnection() {
  try {
    const c = await getClient();
    const result = await c.ping();
    logger.info('Redis: Connection test successful', { result });
    return true;
  } catch (error) {
    logger.error('Redis: Connection test failed', error);
    return false;
  }
}

async function close() {
  if (client) {
    await client.quit();
    client = null;
    isConnected = false;
    logger.info('Redis: Client closed');
  }
}

function isReady() {
  return isConnected;
}

module.exports = {
  createClient,
  getClient,
  get,
  set,
  del,
  exists,
  expire,
  ttl,
  incr,
  decr,
  hSet,
  hGet,
  hGetAll,
  hDel,
  zAdd,
  zRange,
  zRangeByScore,
  zRem,
  zScore,
  lPush,
  rPush,
  lPop,
  rPop,
  lRange,
  testConnection,
  close,
  isReady
};
