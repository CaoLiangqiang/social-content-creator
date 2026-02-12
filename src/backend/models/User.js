const { query, transaction } = require('../config/database');
const logger = require('../utils/logger');

const User = {
  async create(userData) {
    const { username, email, passwordHash, role = 'user' } = userData;
    const sql = `
      INSERT INTO users (username, email, password_hash, role)
      VALUES ($1, $2, $3, $4)
      RETURNING id, username, email, role, created_at
    `;
    const result = await query(sql, [username, email, passwordHash, role]);
    return result.rows[0];
  },

  async findById(id) {
    const sql = `
      SELECT id, username, email, avatar_url, role, status, is_verified, 
             last_login_at, created_at, updated_at
      FROM users WHERE id = $1
    `;
    const result = await query(sql, [id]);
    return result.rows[0] || null;
  },

  async findByEmail(email) {
    const sql = 'SELECT * FROM users WHERE email = $1';
    const result = await query(sql, [email]);
    return result.rows[0] || null;
  },

  async findByUsername(username) {
    const sql = 'SELECT * FROM users WHERE username = $1';
    const result = await query(sql, [username]);
    return result.rows[0] || null;
  },

  async update(id, updates) {
    const fields = [];
    const values = [id];
    let paramCount = 2;

    const allowedFields = ['username', 'email', 'avatar_url', 'role', 'status', 'is_verified'];
    
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
      UPDATE users SET ${fields.join(', ')}
      WHERE id = $1
      RETURNING id, username, email, avatar_url, role, status, updated_at
    `;
    
    const result = await query(sql, values);
    return result.rows[0] || null;
  },

  async updatePassword(id, passwordHash) {
    const sql = `
      UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP
      WHERE id = $2
    `;
    await query(sql, [passwordHash, id]);
  },

  async updateLastLogin(id) {
    const sql = 'UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = $1';
    await query(sql, [id]);
  },

  async delete(id) {
    const sql = "UPDATE users SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE id = $1";
    await query(sql, [id]);
  },

  async list(options = {}) {
    const { page = 1, limit = 20, status, role } = options;
    const offset = (page - 1) * limit;
    
    let whereClause = '1=1';
    const values = [];
    let paramCount = 1;

    if (status) {
      whereClause += ` AND status = $${paramCount}`;
      values.push(status);
      paramCount++;
    }

    if (role) {
      whereClause += ` AND role = $${paramCount}`;
      values.push(role);
      paramCount++;
    }

    const countSql = `SELECT COUNT(*) FROM users WHERE ${whereClause}`;
    const countResult = await query(countSql, values);
    const total = parseInt(countResult.rows[0].count);

    const sql = `
      SELECT id, username, email, avatar_url, role, status, is_verified, created_at
      FROM users
      WHERE ${whereClause}
      ORDER BY created_at DESC
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
};

module.exports = User;
