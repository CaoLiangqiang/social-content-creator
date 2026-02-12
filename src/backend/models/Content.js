const { query } = require('../config/database');
const logger = require('../utils/logger');

const Content = {
  async create(contentData) {
    const {
      platformId,
      platformContentId,
      title,
      content,
      contentType = 'note',
      authorId,
      authorName,
      authorAvatar,
      viewCount = 0,
      likeCount = 0,
      commentCount = 0,
      shareCount = 0,
      collectCount = 0,
      images = [],
      videoUrl,
      coverUrl,
      tags = [],
      topics = [],
      url,
      publishedAt
    } = contentData;

    const sql = `
      INSERT INTO contents (
        platform_id, platform_content_id, title, content, content_type,
        author_id, author_name, author_avatar,
        view_count, like_count, comment_count, share_count, collect_count,
        images, video_url, cover_url, tags, topics, url, published_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
      ON CONFLICT (platform_id, platform_content_id) 
      DO UPDATE SET
        title = EXCLUDED.title,
        content = EXCLUDED.content,
        view_count = EXCLUDED.view_count,
        like_count = EXCLUDED.like_count,
        comment_count = EXCLUDED.comment_count,
        share_count = EXCLUDED.share_count,
        collect_count = EXCLUDED.collect_count,
        updated_at = CURRENT_TIMESTAMP
      RETURNING *
    `;

    const result = await query(sql, [
      platformId, platformContentId, title, content, contentType,
      authorId, authorName, authorAvatar,
      viewCount, likeCount, commentCount, shareCount, collectCount,
      JSON.stringify(images), videoUrl, coverUrl,
      JSON.stringify(tags), JSON.stringify(topics), url, publishedAt
    ]);

    return result.rows[0];
  },

  async findById(id) {
    const sql = 'SELECT * FROM contents WHERE id = $1';
    const result = await query(sql, [id]);
    return result.rows[0] || null;
  },

  async findByPlatformContentId(platformId, platformContentId) {
    const sql = 'SELECT * FROM contents WHERE platform_id = $1 AND platform_content_id = $2';
    const result = await query(sql, [platformId, platformContentId]);
    return result.rows[0] || null;
  },

  async update(id, updates) {
    const fields = [];
    const values = [id];
    let paramCount = 2;

    const allowedFields = [
      'title', 'content', 'view_count', 'like_count', 'comment_count',
      'share_count', 'collect_count', 'images', 'video_url', 'cover_url',
      'tags', 'topics', 'status'
    ];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        if (['images', 'tags', 'topics'].includes(key)) {
          fields.push(`${key} = $${paramCount}::jsonb`);
          values.push(JSON.stringify(value));
        } else {
          fields.push(`${key} = $${paramCount}`);
          values.push(value);
        }
        paramCount++;
      }
    }

    if (fields.length === 0) {
      return this.findById(id);
    }

    fields.push('updated_at = CURRENT_TIMESTAMP');

    const sql = `
      UPDATE contents SET ${fields.join(', ')}
      WHERE id = $1
      RETURNING *
    `;

    const result = await query(sql, values);
    return result.rows[0] || null;
  },

  async delete(id) {
    const sql = "UPDATE contents SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE id = $1";
    await query(sql, [id]);
  },

  async list(options = {}) {
    const {
      page = 1,
      limit = 20,
      platformId,
      contentType,
      status = 'active',
      authorId,
      orderBy = 'published_at',
      orderDir = 'DESC',
      search
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

    if (contentType) {
      whereClauses.push(`content_type = $${paramCount}`);
      values.push(contentType);
      paramCount++;
    }

    if (status) {
      whereClauses.push(`status = $${paramCount}`);
      values.push(status);
      paramCount++;
    }

    if (authorId) {
      whereClauses.push(`author_id = $${paramCount}`);
      values.push(authorId);
      paramCount++;
    }

    if (search) {
      whereClauses.push(`(title ILIKE $${paramCount} OR content ILIKE $${paramCount})`);
      values.push(`%${search}%`);
      paramCount++;
    }

    const whereClause = whereClauses.length > 0 ? whereClauses.join(' AND ') : '1=1';

    const countSql = `SELECT COUNT(*) FROM contents WHERE ${whereClause}`;
    const countResult = await query(countSql, values);
    const total = parseInt(countResult.rows[0].count);

    const validOrderBy = ['published_at', 'created_at', 'view_count', 'like_count', 'comment_count'].includes(orderBy)
      ? orderBy
      : 'published_at';
    const validOrderDir = ['ASC', 'DESC'].includes(orderDir.toUpperCase()) ? orderDir.toUpperCase() : 'DESC';

    const sql = `
      SELECT * FROM contents
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

  async getHotContents(platformId, limit = 10) {
    const sql = `
      SELECT * FROM contents
      WHERE platform_id = $1 AND status = 'active'
      ORDER BY (like_count + comment_count * 2 + share_count * 3) DESC
      LIMIT $2
    `;
    const result = await query(sql, [platformId, limit]);
    return result.rows;
  },

  async getTrendingTags(platformId, limit = 20) {
    const sql = `
      SELECT tag, COUNT(*) as count
      FROM contents, jsonb_array_elements_text(tags) as tag
      WHERE platform_id = $1 AND status = 'active'
      GROUP BY tag
      ORDER BY count DESC
      LIMIT $2
    `;
    const result = await query(sql, [platformId, limit]);
    return result.rows;
  },

  async incrementViewCount(id) {
    const sql = 'UPDATE contents SET view_count = view_count + 1 WHERE id = $1';
    await query(sql, [id]);
  }
};

module.exports = Content;
