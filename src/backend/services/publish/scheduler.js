const { query } = require('../../config/database');
const { redis } = require('../../config');
const logger = require('../../utils/logger');

const QUEUE_KEY = 'publish:queue';
const SCHEDULE_KEY = 'publish:schedule';
const PROCESSING_KEY = 'publish:processing';

class PublishScheduler {
  constructor() {
    this.isRunning = false;
    this.checkInterval = null;
    this.pollIntervalMs = 60000;
  }

  async schedulePublish(publishData) {
    const {
      contentId,
      platformId,
      platformAccountId,
      scheduledTime,
      timezone = 'Asia/Shanghai',
      metadata = {}
    } = publishData;

    if (!contentId || !platformId || !scheduledTime) {
      throw new Error('contentId, platformId and scheduledTime are required');
    }

    const scheduledDate = new Date(scheduledTime);
    if (isNaN(scheduledDate.getTime())) {
      throw new Error('Invalid scheduledTime');
    }

    if (scheduledDate <= new Date()) {
      throw new Error('scheduledTime must be in the future');
    }

    const taskId = `pub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const sql = `
      INSERT INTO publish_tasks (
        id, content_id, platform_id, platform_account_id,
        status, scheduled_time, timezone, metadata
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      RETURNING *
    `;

    const result = await query(sql, [
      taskId,
      contentId,
      platformId,
      platformAccountId,
      'scheduled',
      scheduledDate,
      timezone,
      JSON.stringify(metadata)
    ]);

    const score = scheduledDate.getTime();
    await redis.zAdd(SCHEDULE_KEY, score, taskId);

    logger.info('Publish task scheduled', {
      taskId,
      contentId,
      platformId,
      scheduledTime: scheduledDate.toISOString()
    });

    return result.rows[0];
  }

  async cancelSchedule(taskId) {
    const sql = `
      UPDATE publish_tasks 
      SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
      WHERE id = $1 AND status = 'scheduled'
      RETURNING *
    `;

    const result = await query(sql, [taskId]);

    if (result.rows[0]) {
      await redis.zRem(SCHEDULE_KEY, taskId);
      logger.info('Publish task cancelled', { taskId });
    }

    return result.rows[0];
  }

  async getTask(taskId) {
    const sql = 'SELECT * FROM publish_tasks WHERE id = $1';
    const result = await query(sql, [taskId]);
    return result.rows[0] || null;
  }

  async listTasks(options = {}) {
    const {
      page = 1,
      limit = 20,
      status,
      platformId,
      orderBy = 'scheduled_time',
      orderDir = 'ASC'
    } = options;

    const offset = (page - 1) * limit;
    const whereClauses = [];
    const values = [];
    let paramCount = 1;

    if (status) {
      whereClauses.push(`status = $${paramCount}`);
      values.push(status);
      paramCount++;
    }

    if (platformId) {
      whereClauses.push(`platform_id = $${paramCount}`);
      values.push(platformId);
      paramCount++;
    }

    const whereClause = whereClauses.length > 0 ? whereClauses.join(' AND ') : '1=1';

    const countSql = `SELECT COUNT(*) FROM publish_tasks WHERE ${whereClause}`;
    const countResult = await query(countSql, values);
    const total = parseInt(countResult.rows[0].count);

    const validOrderBy = ['scheduled_time', 'created_at', 'status'].includes(orderBy)
      ? orderBy
      : 'scheduled_time';
    const validOrderDir = ['ASC', 'DESC'].includes(orderDir.toUpperCase()) ? orderDir.toUpperCase() : 'ASC';

    const sql = `
      SELECT pt.*, c.title as content_title, p.name as platform_name
      FROM publish_tasks pt
      LEFT JOIN contents c ON pt.content_id = c.id
      LEFT JOIN platforms p ON pt.platform_id = p.id
      WHERE ${whereClause}
      ORDER BY pt.${validOrderBy} ${validOrderDir}
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
  }

  async getPendingTasks() {
    const now = Date.now();
    const taskIds = await redis.zRangeByScore(SCHEDULE_KEY, 0, now);

    if (taskIds.length === 0) {
      return [];
    }

    const sql = `
      SELECT pt.*, c.title as content_title, c.content, c.images, c.video_url
      FROM publish_tasks pt
      LEFT JOIN contents c ON pt.content_id = c.id
      WHERE pt.id = ANY($1) AND pt.status = 'scheduled'
    `;

    const result = await query(sql, [taskIds]);
    return result.rows;
  }

  async startProcessing(taskId) {
    const sql = `
      UPDATE publish_tasks 
      SET status = 'processing', updated_at = CURRENT_TIMESTAMP
      WHERE id = $1 AND status = 'scheduled'
      RETURNING *
    `;

    const result = await query(sql, [taskId]);

    if (result.rows[0]) {
      await redis.zRem(SCHEDULE_KEY, taskId);
      await redis.hSet(PROCESSING_KEY, taskId, JSON.stringify({
        startTime: Date.now(),
        taskId
      }));
      logger.info('Publish task processing started', { taskId });
    }

    return result.rows[0];
  }

  async completeTask(taskId, result) {
    const { success, publishedUrl, errorMessage } = result;

    const sql = `
      UPDATE publish_tasks 
      SET status = $2, published_url = $3, error_message = $4, 
          published_at = $5, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING *
    `;

    const updateResult = await query(sql, [
      taskId,
      success ? 'completed' : 'failed',
      publishedUrl || null,
      errorMessage || null,
      success ? new Date() : null
    ]);

    await redis.hDel(PROCESSING_KEY, taskId);

    logger.info('Publish task completed', {
      taskId,
      success,
      publishedUrl
    });

    return updateResult.rows[0];
  }

  async retryTask(taskId) {
    const task = await this.getTask(taskId);

    if (!task || task.status !== 'failed') {
      throw new Error('Task not found or not in failed status');
    }

    const newScheduledTime = new Date(Date.now() + 5 * 60 * 1000);

    const sql = `
      UPDATE publish_tasks 
      SET status = 'scheduled', 
          scheduled_time = $2,
          retry_count = retry_count + 1,
          error_message = NULL,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING *
    `;

    const result = await query(sql, [taskId, newScheduledTime]);

    await redis.zAdd(SCHEDULE_KEY, newScheduledTime.getTime(), taskId);

    logger.info('Publish task scheduled for retry', {
      taskId,
      newScheduledTime: newScheduledTime.toISOString()
    });

    return result.rows[0];
  }

  start() {
    if (this.isRunning) {
      logger.warn('Publish scheduler is already running');
      return;
    }

    this.isRunning = true;
    logger.info('Publish scheduler started');

    this.checkInterval = setInterval(async () => {
      try {
        await this.processPendingTasks();
      } catch (error) {
        logger.error('Error processing pending tasks', { error: error.message });
      }
    }, this.pollIntervalMs);

    this.processPendingTasks();
  }

  stop() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    this.isRunning = false;
    logger.info('Publish scheduler stopped');
  }

  async processPendingTasks() {
    const tasks = await this.getPendingTasks();

    if (tasks.length === 0) {
      return;
    }

    logger.info(`Processing ${tasks.length} pending publish tasks`);

    for (const task of tasks) {
      try {
        await this.startProcessing(task.id);

        const result = await this.executePublish(task);

        await this.completeTask(task.id, result);
      } catch (error) {
        logger.error('Failed to process publish task', {
          taskId: task.id,
          error: error.message
        });

        await this.completeTask(task.id, {
          success: false,
          errorMessage: error.message
        });
      }
    }
  }

  async executePublish(task) {
    logger.info('Executing publish', {
      taskId: task.id,
      platformId: task.platform_id
    });

    await new Promise(resolve => setTimeout(resolve, 1000));

    return {
      success: true,
      publishedUrl: `https://platform.com/post/${task.id}`
    };
  }

  getStats() {
    return {
      isRunning: this.isRunning,
      pollIntervalMs: this.pollIntervalMs
    };
  }
}

const publishScheduler = new PublishScheduler();

module.exports = publishScheduler;
module.exports.PublishScheduler = PublishScheduler;
