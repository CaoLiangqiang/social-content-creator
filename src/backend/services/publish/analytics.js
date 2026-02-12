const { query } = require('../config/database');
const { redis } = require('../config');
const logger = require('../utils/logger');

class AnalyticsService {
  constructor() {
    this.cachePrefix = 'analytics:';
    this.cacheTTL = 300;
  }

  async trackPublishResult(taskId, result) {
    const sql = `
      INSERT INTO publish_analytics (
        task_id, platform_id, content_id, published_at,
        initial_views, initial_likes, initial_comments
      )
      SELECT $1, platform_id, content_id, published_at, 0, 0, 0
      FROM publish_tasks WHERE id = $1
      ON CONFLICT (task_id) DO UPDATE SET
        last_tracked_at = CURRENT_TIMESTAMP
      RETURNING *
    `;

    const dbResult = await query(sql, [taskId]);
    return dbResult.rows[0];
  }

  async updateMetrics(taskId, metrics) {
    const { views, likes, comments, shares, collects } = metrics;

    const sql = `
      UPDATE publish_analytics 
      SET 
        current_views = $2,
        current_likes = $3,
        current_comments = $4,
        current_shares = $5,
        current_collects = $6,
        last_tracked_at = CURRENT_TIMESTAMP,
        tracking_count = tracking_count + 1
      WHERE task_id = $1
      RETURNING *
    `;

    const result = await query(sql, [taskId, views, likes, comments, shares, collects]);
    return result.rows[0];
  }

  async getContentAnalytics(contentId) {
    const cacheKey = `${this.cachePrefix}content:${contentId}`;
    const cached = await redis.get(cacheKey);

    if (cached) {
      return cached;
    }

    const sql = `
      SELECT 
        pa.*,
        pt.scheduled_time,
        pt.published_at,
        pt.status,
        c.title as content_title,
        p.name as platform_name
      FROM publish_analytics pa
      JOIN publish_tasks pt ON pa.task_id = pt.id
      JOIN contents c ON pa.content_id = c.id
      JOIN platforms p ON pa.platform_id = p.id
      WHERE pa.content_id = $1
      ORDER BY pa.published_at DESC
    `;

    const result = await query(sql, [contentId]);
    const data = result.rows;

    await redis.set(cacheKey, data, this.cacheTTL);

    return data;
  }

  async getPlatformAnalytics(platformId, options = {}) {
    const { startDate, endDate, groupBy = 'day' } = options;

    const whereClauses = ['pa.platform_id = $1'];
    const values = [platformId];
    let paramCount = 2;

    if (startDate) {
      whereClauses.push(`pa.published_at >= $${paramCount}`);
      values.push(startDate);
      paramCount++;
    }

    if (endDate) {
      whereClauses.push(`pa.published_at <= $${paramCount}`);
      values.push(endDate);
      paramCount++;
    }

    const whereClause = whereClauses.join(' AND ');

    const groupByClause = groupBy === 'hour'
      ? `DATE_TRUNC('hour', pa.published_at)`
      : `DATE_TRUNC('day', pa.published_at)`;

    const sql = `
      SELECT 
        ${groupByClause} as period,
        COUNT(*) as publish_count,
        SUM(pa.current_views) as total_views,
        SUM(pa.current_likes) as total_likes,
        SUM(pa.current_comments) as total_comments,
        AVG(pa.current_views) as avg_views,
        AVG(pa.current_likes) as avg_likes,
        AVG(pa.current_comments) as avg_comments
      FROM publish_analytics pa
      WHERE ${whereClause}
      GROUP BY ${groupByClause}
      ORDER BY period DESC
    `;

    const result = await query(sql, values);
    return result.rows;
  }

  async getOverallStats(options = {}) {
    const { startDate, endDate } = options;

    const whereClauses = [];
    const values = [];
    let paramCount = 1;

    if (startDate) {
      whereClauses.push(`published_at >= $${paramCount}`);
      values.push(startDate);
      paramCount++;
    }

    if (endDate) {
      whereClauses.push(`published_at <= $${paramCount}`);
      values.push(endDate);
      paramCount++;
    }

    const whereClause = whereClauses.length > 0 ? whereClauses.join(' AND ') : '1=1';

    const sql = `
      SELECT 
        COUNT(*) as total_published,
        SUM(current_views) as total_views,
        SUM(current_likes) as total_likes,
        SUM(current_comments) as total_comments,
        SUM(current_shares) as total_shares,
        AVG(current_views) as avg_views,
        AVG(current_likes) as avg_likes,
        AVG(current_comments) as avg_comments
      FROM publish_analytics
      WHERE ${whereClause}
    `;

    const result = await query(sql, values);
    return result.rows[0];
  }

  async getTopContent(limit = 10, metric = 'views') {
    const validMetrics = ['views', 'likes', 'comments', 'shares'];
    if (!validMetrics.includes(metric)) {
      metric = 'views';
    }

    const sql = `
      SELECT 
        pa.content_id,
        c.title,
        c.cover_url,
        p.name as platform_name,
        pa.current_views,
        pa.current_likes,
        pa.current_comments,
        pa.current_shares,
        pa.published_at
      FROM publish_analytics pa
      JOIN contents c ON pa.content_id = c.id
      JOIN platforms p ON pa.platform_id = p.id
      ORDER BY pa.current_${metric} DESC
      LIMIT $1
    `;

    const result = await query(sql, [limit]);
    return result.rows;
  }

  async getEngagementRate(taskId) {
    const sql = `
      SELECT 
        current_views,
        current_likes,
        current_comments,
        current_shares,
        CASE 
          WHEN current_views > 0 
          THEN ROUND((current_likes + current_comments + current_shares)::float / current_views * 100, 2)
          ELSE 0 
        END as engagement_rate
      FROM publish_analytics
      WHERE task_id = $1
    `;

    const result = await query(sql, [taskId]);
    return result.rows[0];
  }

  async getPublishTrend(days = 30) {
    const sql = `
      SELECT 
        DATE_TRUNC('day', published_at) as date,
        COUNT(*) as publish_count,
        SUM(current_views) as views,
        SUM(current_likes) as likes
      FROM publish_analytics
      WHERE published_at >= CURRENT_DATE - INTERVAL '${days} days'
      GROUP BY DATE_TRUNC('day', published_at)
      ORDER BY date
    `;

    const result = await query(sql, []);
    return result.rows;
  }

  async generateReport(options = {}) {
    const { platformId, startDate, endDate, reportType = 'summary' } = options;

    const overallStats = await this.getOverallStats({ startDate, endDate });
    const topContent = await this.getTopContent(10, 'views');
    const trend = await this.getPublishTrend(30);

    let platformStats = null;
    if (platformId) {
      platformStats = await this.getPlatformAnalytics(platformId, { startDate, endDate });
    }

    const report = {
      generatedAt: new Date().toISOString(),
      period: {
        startDate: startDate || 'all time',
        endDate: endDate || 'now'
      },
      summary: {
        totalPublished: parseInt(overallStats.total_published) || 0,
        totalViews: parseInt(overallStats.total_views) || 0,
        totalLikes: parseInt(overallStats.total_likes) || 0,
        totalComments: parseInt(overallStats.total_comments) || 0,
        avgViews: parseFloat(overallStats.avg_views) || 0,
        avgLikes: parseFloat(overallStats.avg_likes) || 0,
        avgEngagementRate: overallStats.total_views > 0
          ? ((parseInt(overallStats.total_likes) + parseInt(overallStats.total_comments)) / parseInt(overallStats.total_views) * 100).toFixed(2)
          : 0
      },
      topContent,
      trend,
      platformStats
    };

    return report;
  }

  async cleanupOldData(daysToKeep = 365) {
    const sql = `
      DELETE FROM publish_analytics
      WHERE published_at < CURRENT_DATE - INTERVAL '${daysToKeep} days'
      RETURNING COUNT(*)
    `;

    const result = await query(sql, []);
    const deleted = parseInt(result.rows[0]?.count || 0);

    logger.info('Analytics cleanup completed', { deletedRecords: deleted });

    return deleted;
  }
}

module.exports = new AnalyticsService();
module.exports.AnalyticsService = AnalyticsService;
