const { query } = require('../config/database');
const logger = require('../utils/logger');

const AnalysisResult = {
  async create(data) {
    const {
      contentId,
      sentimentScore,
      sentimentLabel,
      sentimentConfidence,
      keywords = [],
      topics = [],
      qualityScore,
      engagementRate,
      viralScore,
      viralFactors
    } = data;

    const sql = `
      INSERT INTO analysis_results (
        content_id, sentiment_score, sentiment_label, sentiment_confidence,
        keywords, topics, quality_score, engagement_rate, viral_score, viral_factors
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      ON CONFLICT (content_id) 
      DO UPDATE SET
        sentiment_score = EXCLUDED.sentiment_score,
        sentiment_label = EXCLUDED.sentiment_label,
        sentiment_confidence = EXCLUDED.sentiment_confidence,
        keywords = EXCLUDED.keywords,
        topics = EXCLUDED.topics,
        quality_score = EXCLUDED.quality_score,
        engagement_rate = EXCLUDED.engagement_rate,
        viral_score = EXCLUDED.viral_score,
        viral_factors = EXCLUDED.viral_factors,
        analyzed_at = CURRENT_TIMESTAMP
      RETURNING *
    `;

    const result = await query(sql, [
      contentId, sentimentScore, sentimentLabel, sentimentConfidence,
      JSON.stringify(keywords), JSON.stringify(topics),
      qualityScore, engagementRate, viralScore,
      viralFactors ? JSON.stringify(viralFactors) : null
    ]);

    return result.rows[0];
  },

  async findById(id) {
    const sql = 'SELECT * FROM analysis_results WHERE id = $1';
    const result = await query(sql, [id]);
    return result.rows[0] || null;
  },

  async findByContentId(contentId) {
    const sql = 'SELECT * FROM analysis_results WHERE content_id = $1';
    const result = await query(sql, [contentId]);
    return result.rows[0] || null;
  },

  async list(options = {}) {
    const {
      page = 1,
      limit = 20,
      sentimentLabel,
      minQualityScore,
      minViralScore,
      orderBy = 'analyzed_at',
      orderDir = 'DESC'
    } = options;

    const offset = (page - 1) * limit;
    const whereClauses = [];
    const values = [];
    let paramCount = 1;

    if (sentimentLabel) {
      whereClauses.push(`sentiment_label = $${paramCount}`);
      values.push(sentimentLabel);
      paramCount++;
    }

    if (minQualityScore !== undefined) {
      whereClauses.push(`quality_score >= $${paramCount}`);
      values.push(minQualityScore);
      paramCount++;
    }

    if (minViralScore !== undefined) {
      whereClauses.push(`viral_score >= $${paramCount}`);
      values.push(minViralScore);
      paramCount++;
    }

    const whereClause = whereClauses.length > 0 ? whereClauses.join(' AND ') : '1=1';

    const countSql = `SELECT COUNT(*) FROM analysis_results WHERE ${whereClause}`;
    const countResult = await query(countSql, values);
    const total = parseInt(countResult.rows[0].count);

    const validOrderBy = ['analyzed_at', 'quality_score', 'viral_score', 'sentiment_score'].includes(orderBy)
      ? orderBy
      : 'analyzed_at';
    const validOrderDir = ['ASC', 'DESC'].includes(orderDir.toUpperCase()) ? orderDir.toUpperCase() : 'DESC';

    const sql = `
      SELECT ar.*, c.title, c.author_name, c.platform_id
      FROM analysis_results ar
      LEFT JOIN contents c ON ar.content_id = c.id
      WHERE ${whereClause}
      ORDER BY ar.${validOrderBy} ${validOrderDir}
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

  async getTopViral(limit = 10) {
    const sql = `
      SELECT ar.*, c.title, c.author_name, c.platform_id, c.url
      FROM analysis_results ar
      LEFT JOIN contents c ON ar.content_id = c.id
      WHERE ar.viral_score IS NOT NULL
      ORDER BY ar.viral_score DESC
      LIMIT $1
    `;
    const result = await query(sql, [limit]);
    return result.rows;
  },

  async getSentimentDistribution() {
    const sql = `
      SELECT sentiment_label, COUNT(*) as count
      FROM analysis_results
      WHERE sentiment_label IS NOT NULL
      GROUP BY sentiment_label
    `;
    const result = await query(sql);
    return result.rows;
  },

  async getAverageScores() {
    const sql = `
      SELECT 
        AVG(quality_score) as avg_quality,
        AVG(viral_score) as avg_viral,
        AVG(engagement_rate) as avg_engagement,
        AVG(sentiment_score) as avg_sentiment
      FROM analysis_results
    `;
    const result = await query(sql);
    return result.rows[0];
  },

  async delete(id) {
    const sql = 'DELETE FROM analysis_results WHERE id = $1';
    await query(sql, [id]);
  },

  async deleteByContentId(contentId) {
    const sql = 'DELETE FROM analysis_results WHERE content_id = $1';
    await query(sql, [contentId]);
  }
};

module.exports = AnalysisResult;
