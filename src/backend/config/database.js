const { Pool } = require('pg');
const logger = require('../utils/logger');

const pgConfig = {
  host: process.env.PG_HOST || 'localhost',
  port: parseInt(process.env.PG_PORT || '5432'),
  database: process.env.PG_DATABASE || 'social_content',
  user: process.env.PG_USER || 'postgres',
  password: process.env.PG_PASSWORD || 'postgres',
  max: parseInt(process.env.PG_POOL_MAX || '20'),
  min: parseInt(process.env.PG_POOL_MIN || '5'),
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
};

const pool = new Pool(pgConfig);

pool.on('connect', () => {
  logger.info('PostgreSQL: New client connected');
});

pool.on('error', (err) => {
  logger.error('PostgreSQL: Unexpected error on idle client', err);
});

pool.on('remove', () => {
  logger.debug('PostgreSQL: Client removed from pool');
});

async function query(text, params) {
  const start = Date.now();
  const result = await pool.query(text, params);
  const duration = Date.now() - start;
  
  logger.debug(`PostgreSQL: Query executed in ${duration}ms`, {
    query: text.substring(0, 100),
    rows: result.rowCount
  });
  
  return result;
}

async function transaction(callback) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

async function getClient() {
  return pool.connect();
}

async function testConnection() {
  try {
    const result = await query('SELECT NOW()');
    logger.info('PostgreSQL: Connection test successful', {
      timestamp: result.rows[0].now
    });
    return true;
  } catch (error) {
    logger.error('PostgreSQL: Connection test failed', error);
    return false;
  }
}

async function close() {
  await pool.end();
  logger.info('PostgreSQL: Pool closed');
}

module.exports = {
  pool,
  query,
  transaction,
  getClient,
  testConnection,
  close
};
