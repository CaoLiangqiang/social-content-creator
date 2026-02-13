const express = require('express');
const router = express.Router();
const { query } = require('../config/database');
const { authenticate } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const logger = require('../utils/logger');

/**
 * 获取内容列表
 * GET /api/v1/contents
 */
router.get('/', authenticate, asyncHandler(async (req, res) => {
  const { 
    page = 1, 
    limit = 20, 
    platform, 
    contentType,
    keyword,
    sortBy = 'created_at',
    sortOrder = 'desc'
  } = req.query;

  const offset = (parseInt(page) - 1) * parseInt(limit);
  const params = [];
  let whereClause = '';

  // 平台筛选
  if (platform) {
    whereClause += ` AND c.platform_id = (SELECT id FROM platforms WHERE name = $${params.length + 1})`;
    params.push(platform);
  }

  // 内容类型筛选
  if (contentType) {
    whereClause += ` AND c.content_type = $${params.length + 1}`;
    params.push(contentType);
  }

  // 关键词搜索
  if (keyword) {
    whereClause += ` AND (c.title ILIKE $${params.length + 1} OR c.content ILIKE $${params.length + 1})`;
    params.push(`%${keyword}%`);
  }

  // 排序
  const validSortColumns = ['created_at', 'published_at', 'view_count', 'like_count'];
  const orderColumn = validSortColumns.includes(sortBy) ? sortBy : 'created_at';
  const orderDirection = sortOrder.toLowerCase() === 'asc' ? 'ASC' : 'DESC';

  // 获取总数
  const countResult = await query(
    `SELECT COUNT(*) FROM contents c WHERE 1=1 ${whereClause}`,
    params
  );
  const total = parseInt(countResult.rows[0].count);

  // 获取列表
  const result = await query(
    `SELECT c.*, p.name as platform_name 
     FROM contents c
     LEFT JOIN platforms p ON c.platform_id = p.id
     WHERE 1=1 ${whereClause}
     ORDER BY c.${orderColumn} ${orderDirection}
     LIMIT $${params.length + 1} OFFSET $${params.length + 2}`,
    [...params, parseInt(limit), offset]
  );

  res.json({
    success: true,
    data: {
      list: result.rows.map(item => ({
        id: item.id,
        platform: item.platform_name,
        platformContentId: item.platform_content_id,
        title: item.title,
        content: item.content,
        contentType: item.content_type,
        authorName: item.author_name,
        authorAvatar: item.author_avatar,
        viewCount: item.view_count,
        likeCount: item.like_count,
        commentCount: item.comment_count,
        shareCount: item.share_count,
        collectCount: item.collect_count,
        coverUrl: item.cover_url,
        tags: item.tags,
        url: item.url,
        publishedAt: item.published_at,
        createdAt: item.created_at
      })),
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        totalPages: Math.ceil(total / parseInt(limit))
      }
    }
  });
}));

/**
 * 获取内容详情
 * GET /api/v1/contents/:id
 */
router.get('/:id', authenticate, asyncHandler(async (req, res) => {
  const { id } = req.params;

  const result = await query(
    `SELECT c.*, p.name as platform_name 
     FROM contents c
     LEFT JOIN platforms p ON c.platform_id = p.id
     WHERE c.id = $1`,
    [id]
  );

  if (result.rows.length === 0) {
    return res.status(404).json({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: 'Content not found'
      }
    });
  }

  const item = result.rows[0];

  res.json({
    success: true,
    data: {
      id: item.id,
      platform: item.platform_name,
      platformContentId: item.platform_content_id,
      title: item.title,
      content: item.content,
      contentType: item.content_type,
      authorId: item.author_id,
      authorName: item.author_name,
      authorAvatar: item.author_avatar,
      viewCount: item.view_count,
      likeCount: item.like_count,
      commentCount: item.comment_count,
      shareCount: item.share_count,
      collectCount: item.collect_count,
      images: item.images,
      coverUrl: item.cover_url,
      videoUrl: item.video_url,
      tags: item.tags,
      topics: item.topics,
      url: item.url,
      publishedAt: item.published_at,
      crawledAt: item.crawled_at,
      createdAt: item.created_at,
      updatedAt: item.updated_at
    }
  });
}));

/**
 * 更新内容
 * PUT /api/v1/contents/:id
 */
router.put('/:id', authenticate, asyncHandler(async (req, res) => {
  const { id } = req.params;
  const { title, content, tags } = req.body;

  // 检查内容是否存在
  const checkResult = await query(
    'SELECT id FROM contents WHERE id = $1',
    [id]
  );

  if (checkResult.rows.length === 0) {
    return res.status(404).json({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: 'Content not found'
      }
    });
  }

  // 构建更新字段
  const updates = [];
  const params = [id];
  let paramIndex = 2;

  if (title !== undefined) {
    updates.push(`title = $${paramIndex++}`);
    params.push(title);
  }

  if (content !== undefined) {
    updates.push(`content = $${paramIndex++}`);
    params.push(content);
  }

  if (tags !== undefined) {
    updates.push(`tags = $${paramIndex++}`);
    params.push(JSON.stringify(tags));
  }

  if (updates.length === 0) {
    return res.status(400).json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'No fields to update'
      }
    });
  }

  updates.push(`updated_at = CURRENT_TIMESTAMP`);

  const result = await query(
    `UPDATE contents SET ${updates.join(', ')} WHERE id = $1 RETURNING *`,
    params
  );

  logger.info(`Content updated: ${id}`, { userId: req.user.userId });

  res.json({
    success: true,
    data: {
      id: result.rows[0].id,
      title: result.rows[0].title,
      content: result.rows[0].content,
      tags: result.rows[0].tags,
      updatedAt: result.rows[0].updated_at
    },
    message: 'Content updated successfully'
  });
}));

/**
 * 删除内容
 * DELETE /api/v1/contents/:id
 */
router.delete('/:id', authenticate, asyncHandler(async (req, res) => {
  const { id } = req.params;

  const result = await query(
    'DELETE FROM contents WHERE id = $1 RETURNING id',
    [id]
  );

  if (result.rows.length === 0) {
    return res.status(404).json({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: 'Content not found'
      }
    });
  }

  logger.info(`Content deleted: ${id}`, { userId: req.user.userId });

  res.json({
    success: true,
    message: 'Content deleted successfully'
  });
}));

/**
 * 获取平台列表
 * GET /api/v1/contents/platforms/list
 */
router.get('/platforms/list', authenticate, asyncHandler(async (req, res) => {
  const result = await query(
    'SELECT id, name, display_name, base_url FROM platforms WHERE is_active = true ORDER BY id'
  );

  res.json({
    success: true,
    data: result.rows.map(platform => ({
      id: platform.id,
      name: platform.name,
      displayName: platform.display_name,
      baseUrl: platform.base_url
    }))
  });
}));

module.exports = router;
