const { spawn } = require('child_process');
const path = require('path');
const logger = require('../../utils/logger');

const PROJECT_ROOT = path.resolve(__dirname, '../../../../..');
const CLI_SCRIPT = path.join(PROJECT_ROOT, 'src/crawler/cli.py');

class CrawlerService {
  constructor() {
    this.activeJobs = new Map();
  }

  async executePython(args = [], timeout = 60000) {
    return new Promise((resolve, reject) => {
      logger.info(`Executing Python CLI: ${CLI_SCRIPT}`, { args });
      
      const pythonProcess = spawn('python3', [CLI_SCRIPT, ...args], {
        cwd: PROJECT_ROOT,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
      });

      let stdout = '';
      let stderr = '';
      let timedOut = false;

      const timeoutId = setTimeout(() => {
        timedOut = true;
        pythonProcess.kill();
        logger.error(`Python process timed out after ${timeout}ms`);
        reject(new Error(`Python process timed out after ${timeout}ms`));
      }, timeout);

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        logger.debug(`Python stderr: ${data.toString()}`);
      });

      pythonProcess.on('close', (code) => {
        clearTimeout(timeoutId);
        if (timedOut) return;
        
        if (code === 0) {
          try {
            const result = stdout.trim() ? JSON.parse(stdout) : { success: true };
            resolve(result);
          } catch (error) {
            resolve({ 
              success: true, 
              rawOutput: stdout,
              message: 'Script executed successfully but output is not JSON'
            });
          }
        } else {
          logger.error(`Python script failed with code ${code}`, { stderr });
          reject(new Error(stderr || `Python script exited with code ${code}`));
        }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeoutId);
        logger.error('Failed to start Python process', error);
        reject(error);
      });
    });
  }

  async crawlBilibiliVideo(bvid) {
    try {
      const result = await this.executePython([
        '--platform', 'bilibili',
        '--type', 'video',
        '--bvid', bvid
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlBilibiliUser(mid) {
    try {
      const result = await this.executePython([
        '--platform', 'bilibili',
        '--type', 'user',
        '--mid', mid
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async searchBilibili(keyword, limit = 20) {
    try {
      const result = await this.executePython([
        '--platform', 'bilibili',
        '--type', 'search',
        '--keyword', keyword,
        '--limit', String(limit)
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlDouyinVideo(url) {
    try {
      const result = await this.executePython([
        '--platform', 'douyin',
        '--type', 'video',
        '--url', url
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlDouyinUser(userId) {
    try {
      const result = await this.executePython([
        '--platform', 'douyin',
        '--type', 'user',
        '--user-id', userId
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlDouyinComments(videoId, limit = 100) {
    try {
      const result = await this.executePython([
        '--platform', 'douyin',
        '--type', 'comments',
        '--video-id', videoId,
        '--limit', String(limit)
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlDouyinUserVideos(userId, limit = 50) {
    try {
      const result = await this.executePython([
        '--platform', 'douyin',
        '--type', 'user-videos',
        '--user-id', userId,
        '--limit', String(limit)
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlXiaohongshuNote(noteId) {
    try {
      const result = await this.executePython([
        '--platform', 'xiaohongshu',
        '--type', 'note',
        '--note-id', noteId
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlXiaohongshuUser(userId) {
    try {
      const result = await this.executePython([
        '--platform', 'xiaohongshu',
        '--type', 'user',
        '--user-id', userId
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async searchXiaohongshu(keyword, limit = 20) {
    try {
      const result = await this.executePython([
        '--platform', 'xiaohongshu',
        '--type', 'search',
        '--keyword', keyword,
        '--limit', String(limit)
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlXiaohongshuComments(noteId, limit = 100) {
    try {
      const result = await this.executePython([
        '--platform', 'xiaohongshu',
        '--type', 'comments',
        '--note-id', noteId,
        '--limit', String(limit)
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async crawlByUrl(url) {
    try {
      const result = await this.executePython([
        '--platform', 'auto',
        '--url', url
      ]);
      return { success: true, data: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  cancelJob(jobId) {
    const job = this.activeJobs.get(jobId);
    if (job) {
      job.kill();
      this.activeJobs.delete(jobId);
      return true;
    }
    return false;
  }

  getActiveJobs() {
    return Array.from(this.activeJobs.keys());
  }

  getSupportedPlatforms() {
    return [
      { 
        code: 'bilibili', 
        name: '哔哩哔哩', 
        enabled: true, 
        features: [
          { type: 'video', name: '视频爬取', params: ['bvid', 'url'] },
          { type: 'user', name: '用户爬取', params: ['mid', 'url'] },
          { type: 'search', name: '关键词搜索', params: ['keyword'] }
        ]
      },
      { 
        code: 'douyin', 
        name: '抖音', 
        enabled: true, 
        features: [
          { type: 'video', name: '视频爬取', params: ['url', 'video_id'] },
          { type: 'user', name: '用户爬取', params: ['user_id', 'url'] },
          { type: 'comments', name: '评论爬取', params: ['video_id'] },
          { type: 'user-videos', name: '用户视频列表', params: ['user_id'] }
        ]
      },
      { 
        code: 'xiaohongshu', 
        name: '小红书', 
        enabled: true, 
        features: [
          { type: 'note', name: '笔记爬取', params: ['note_id', 'url'] },
          { type: 'user', name: '用户爬取', params: ['user_id'] },
          { type: 'search', name: '关键词搜索', params: ['keyword'] },
          { type: 'comments', name: '评论爬取', params: ['note_id'] }
        ]
      }
    ];
  }
}

module.exports = new CrawlerService();
