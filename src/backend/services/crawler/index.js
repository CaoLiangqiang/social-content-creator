const { spawn } = require('child_process');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const logger = require('../../utils/logger');
const { query } = require('../../config/database');
const redis = require('../../config/redis');

const PROJECT_ROOT = path.resolve(__dirname, '../../../../..');
const CLI_SCRIPT = path.join(PROJECT_ROOT, 'src/crawler/cli.py');

// 根据操作系统选择正确的Python命令
const PYTHON_CMD = process.platform === 'win32' ? 'python' : 'python3';

class CrawlerService {
  constructor() {
    this.activeJobs = new Map();
  }

  async executePython(args = [], timeout = 60000) {
    return new Promise((resolve, reject) => {
      logger.info(`Executing Python CLI: ${CLI_SCRIPT}`, { args, pythonCmd: PYTHON_CMD });
      
      const pythonProcess = spawn(PYTHON_CMD, [CLI_SCRIPT, ...args], {
        cwd: PROJECT_ROOT,
        env: { ...process.env, PYTHONPATH: PROJECT_ROOT }
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
        logger.debug('Python stdout:', data.toString());
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        logger.error('Python stderr:', data.toString());
      });

      const timeoutId = setTimeout(() => {
        pythonProcess.kill();
        reject(new Error(`Python execution timeout after ${timeout}ms`));
      }, timeout);

      pythonProcess.on('close', (code) => {
        clearTimeout(timeoutId);
        
        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        } else {
          try {
            const result = JSON.parse(stdout);
            resolve(result);
          } catch (error) {
            resolve({ stdout, stderr });
          }
        }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeoutId);
        reject(error);
      });
    });
  }

  async createJob(platform, type, target, config = {}) {
    const jobId = uuidv4();
    const { maxItems = 20, options = {} } = config;
    
    try {
      // 保存任务到数据库
      await query(
        `INSERT INTO crawler_jobs (id, platform_id, job_type, target, config, max_items, status, progress)
         VALUES ($1, (SELECT id FROM platforms WHERE name = $2), $3, $4, $5, $6, 'pending', 0)`,
        [jobId, platform, type, target, JSON.stringify(options), maxItems]
      );

      // 将任务添加到Redis队列
      await redis.client.lPush('crawler:queue', JSON.stringify({
        jobId,
        platform,
        type,
        target,
        maxItems,
        options
      }));

      logger.info(`Crawler job created: ${jobId}`, { platform, type, target });
      
      return {
        jobId,
        status: 'pending',
        platform,
        type,
        message: 'Task submitted successfully'
      };
    } catch (error) {
      logger.error('Failed to create crawler job:', error);
      throw error;
    }
  }

  async getJobStatus(jobId) {
    try {
      const result = await query(
        `SELECT * FROM crawler_jobs WHERE id = $1`,
        [jobId]
      );

      if (result.rows.length === 0) {
        return null;
      }

      const job = result.rows[0];
      return {
        id: job.id,
        platform: job.platform_id,
        jobType: job.job_type,
        target: job.target,
        status: job.status,
        progress: parseFloat(job.progress),
        totalCrawled: job.total_crawled,
        successCount: job.success_count,
        failedCount: job.failed_count,
        errorMessage: job.error_message,
        startedAt: job.started_at,
        completedAt: job.completed_at,
        createdAt: job.created_at
      };
    } catch (error) {
      logger.error('Failed to get job status:', error);
      throw error;
    }
  }

  async getJobs(page = 1, limit = 20, filters = {}) {
    try {
      const offset = (page - 1) * limit;
      const { status, platform } = filters;
      
      let whereClause = '';
      const params = [];
      
      if (status) {
        whereClause += ' AND status = $' + (params.length + 1);
        params.push(status);
      }
      
      if (platform) {
        whereClause += ' AND platform_id = (SELECT id FROM platforms WHERE name = $' + (params.length + 1) + ')';
        params.push(platform);
      }

      const countResult = await query(
        `SELECT COUNT(*) FROM crawler_jobs WHERE 1=1 ${whereClause}`,
        params
      );
      
      const total = parseInt(countResult.rows[0].count);

      const result = await query(
        `SELECT cj.*, p.name as platform_name 
         FROM crawler_jobs cj
         LEFT JOIN platforms p ON cj.platform_id = p.id
         WHERE 1=1 ${whereClause}
         ORDER BY cj.created_at DESC
         LIMIT $${params.length + 1} OFFSET $${params.length + 2}`,
        [...params, limit, offset]
      );

      return {
        list: result.rows.map(job => ({
          id: job.id,
          platform: job.platform_name,
          jobType: job.job_type,
          target: job.target,
          status: job.status,
          progress: parseFloat(job.progress),
          totalCrawled: job.total_crawled,
          createdAt: job.created_at
        })),
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit)
        }
      };
    } catch (error) {
      logger.error('Failed to get jobs:', error);
      throw error;
    }
  }

  async cancelJob(jobId) {
    try {
      const result = await query(
        `UPDATE crawler_jobs 
         SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
         WHERE id = $1 AND status IN ('pending', 'running')
         RETURNING *`,
        [jobId]
      );

      if (result.rows.length === 0) {
        throw new Error('Job not found or cannot be cancelled');
      }

      // 从Redis队列中移除（如果是pending状态）
      await this.removeFromQueue(jobId);

      logger.info(`Crawler job cancelled: ${jobId}`);
      
      return { success: true, message: 'Job cancelled successfully' };
    } catch (error) {
      logger.error('Failed to cancel job:', error);
      throw error;
    }
  }

  async removeFromQueue(jobId) {
    try {
      const queueItems = await redis.client.lRange('crawler:queue', 0, -1);
      for (const item of queueItems) {
        const job = JSON.parse(item);
        if (job.jobId === jobId) {
          await redis.client.lRem('crawler:queue', 0, item);
          break;
        }
      }
    } catch (error) {
      logger.error('Failed to remove job from queue:', error);
    }
  }

  async crawlByUrl(url) {
    try {
      const result = await this.executePython(['--url', url], 120000);
      return result;
    } catch (error) {
      logger.error('Failed to crawl by URL:', error);
      throw error;
    }
  }

  async crawlBilibiliVideo(bvid) {
    return this.createJob('bilibili', 'video', bvid);
  }

  async crawlBilibiliUser(mid) {
    return this.createJob('bilibili', 'user', mid);
  }

  async searchBilibili(keyword, limit = 20) {
    return this.createJob('bilibili', 'search', keyword, { maxItems: limit });
  }

  async crawlXiaohongshuNote(noteId) {
    return this.createJob('xiaohongshu', 'note', noteId);
  }

  async crawlXiaohongshuUser(userId) {
    return this.createJob('xiaohongshu', 'user', userId);
  }

  async searchXiaohongshu(keyword, limit = 20) {
    return this.createJob('xiaohongshu', 'search', keyword, { maxItems: limit });
  }
}

module.exports = new CrawlerService();
