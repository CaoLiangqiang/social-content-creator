const { query } = require('../config/database');
const logger = require('../utils/logger');

const CrawlerJob = {
  async create(jobData) {
    const {
      platformId,
      jobType,
      target,
      config = {},
      maxItems = 100
    } = jobData;

    const sql = `
      INSERT INTO crawler_jobs (platform_id, job_type, target, config, max_items)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING *
    `;

    const result = await query(sql, [
      platformId, jobType, target, JSON.stringify(config), maxItems
    ]);

    return result.rows[0];
  },

  async findById(id) {
    const sql = 'SELECT * FROM crawler_jobs WHERE id = $1';
    const result = await query(sql, [id]);
    return result.rows[0] || null;
  },

  async update(id, updates) {
    const fields = [];
    const values = [id];
    let paramCount = 2;

    const allowedFields = [
      'status', 'progress', 'total_crawled', 'success_count', 'failed_count',
      'error_message', 'error_stack', 'started_at', 'completed_at'
    ];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        fields.push(`${key} = $${paramCount}`);
        values.push(value);
        paramCount++;
      }
    }

    if (fields.length === 0) {
      return this.findById(id);
    }

    fields.push('updated_at = CURRENT_TIMESTAMP');

    const sql = `
      UPDATE crawler_jobs SET ${fields.join(', ')}
      WHERE id = $1
      RETURNING *
    `;

    const result = await query(sql, values);
    return result.rows[0] || null;
  },

  async start(id) {
    const sql = `
      UPDATE crawler_jobs 
      SET status = 'running', started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING *
    `;
    const result = await query(sql, [id]);
    return result.rows[0];
  },

  async complete(id, stats) {
    const { totalCrawled, successCount, failedCount } = stats;
    const sql = `
      UPDATE crawler_jobs 
      SET status = 'completed', progress = 100,
          total_crawled = $2, success_count = $3, failed_count = $4,
          completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING *
    `;
    const result = await query(sql, [id, totalCrawled, successCount, failedCount]);
    return result.rows[0];
  },

  async fail(id, errorMessage, errorStack = null) {
    const sql = `
      UPDATE crawler_jobs 
      SET status = 'failed', error_message = $2, error_stack = $3,
          completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING *
    `;
    const result = await query(sql, [id, errorMessage, errorStack]);
    return result.rows[0];
  },

  async cancel(id) {
    const sql = `
      UPDATE crawler_jobs 
      SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING *
    `;
    const result = await query(sql, [id]);
    return result.rows[0];
  },

  async updateProgress(id, progress, totalCrawled, successCount, failedCount) {
    const sql = `
      UPDATE crawler_jobs 
      SET progress = $2, total_crawled = $3, success_count = $4, failed_count = $5,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING *
    `;
    const result = await query(sql, [id, progress, totalCrawled, successCount, failedCount]);
    return result.rows[0];
  },

  async list(options = {}) {
    const {
      page = 1,
      limit = 20,
      platformId,
      status,
      jobType,
      orderBy = 'created_at',
      orderDir = 'DESC'
    } = options;

    const offset = (page - 1) * limit;
    const whereClauses = [];
    const values = [];
    let paramCount = 1;

    if (platformId) {
      whereClauses.push(`platform_id = $${paramCount}`);
      values.push(platformId);
      paramCount++;
    }

    if (status) {
      whereClauses.push(`status = $${paramCount}`);
      values.push(status);
      paramCount++;
    }

    if (jobType) {
      whereClauses.push(`job_type = $${paramCount}`);
      values.push(jobType);
      paramCount++;
    }

    const whereClause = whereClauses.length > 0 ? whereClauses.join(' AND ') : '1=1';

    const countSql = `SELECT COUNT(*) FROM crawler_jobs WHERE ${whereClause}`;
    const countResult = await query(countSql, values);
    const total = parseInt(countResult.rows[0].count);

    const validOrderBy = ['created_at', 'updated_at', 'status', 'progress'].includes(orderBy)
      ? orderBy
      : 'created_at';
    const validOrderDir = ['ASC', 'DESC'].includes(orderDir.toUpperCase()) ? orderDir.toUpperCase() : 'DESC';

    const sql = `
      SELECT * FROM crawler_jobs
      WHERE ${whereClause}
      ORDER BY ${validOrderBy} ${validOrderDir}
      LIMIT $${paramCount} OFFSET $${paramCount + 1}
    `;
    values.push(limit, offset);

    const result = await query(sql, values);

    return {
      data: result.rows,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit)
      }
    };
  },

  async getRunningJobs() {
    const sql = `
      SELECT * FROM crawler_jobs 
      WHERE status = 'running' OR status = 'pending'
      ORDER BY created_at ASC
    `;
    const result = await query(sql);
    return result.rows;
  },

  async getStats(platformId = null) {
    let whereClause = '1=1';
    const values = [];

    if (platformId) {
      whereClause = 'platform_id = $1';
      values.push(platformId);
    }

    const sql = `
      SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'pending') as pending,
        COUNT(*) FILTER (WHERE status = 'running') as running,
        COUNT(*) FILTER (WHERE status = 'completed') as completed,
        COUNT(*) FILTER (WHERE status = 'failed') as failed,
        COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
        SUM(total_crawled) as total_crawled,
        SUM(success_count) as total_success,
        SUM(failed_count) as total_failed
      FROM crawler_jobs
      WHERE ${whereClause}
    `;

    const result = await query(sql, values);
    return result.rows[0];
  },

  async delete(id) {
    const sql = 'DELETE FROM crawler_jobs WHERE id = $1';
    await query(sql, [id]);
  },

  async cleanupOld(days = 30) {
    const sql = `
      DELETE FROM crawler_jobs 
      WHERE created_at < NOW() - INTERVAL '${days} days'
      AND status IN ('completed', 'failed', 'cancelled')
    `;
    const result = await query(sql);
    return result.rowCount;
  }
};

module.exports = CrawlerJob;
