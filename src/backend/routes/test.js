const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');
const { pg, mongo, redis } = require('../config');
const { User, Content, CrawlerJob, AnalysisResult } = require('../models');

const TEST_SECRET = process.env.TEST_SECRET;
const isProduction = process.env.NODE_ENV === 'production';

function testAuth(req, res, next) {
  if (isProduction) {
    const secret = req.headers['x-test-secret'] || req.query.secret;
    if (!TEST_SECRET || secret !== TEST_SECRET) {
      return res.status(403).json({
        success: false,
        error: 'Test access denied in production'
      });
    }
  }
  next();
}

router.get('/health', testAuth, async (req, res) => {
  const results = {
    timestamp: new Date().toISOString(),
    tests: {}
  };
  
  results.tests.postgresql = await testPostgreSQL();
  results.tests.mongodb = await testMongoDB();
  results.tests.redis = await testRedis();
  
  const allPassed = Object.values(results.tests).every(t => t.status === 'passed');
  results.overall = allPassed ? 'passed' : 'failed';
  
  res.json({
    success: allPassed,
    data: results
  });
});

async function testPostgreSQL() {
  const timer = logger.startTimer('test:postgresql');
  try {
    const result = await pg.query('SELECT NOW() as now, 1+1 as test');
    const time = logger.endTimer(timer);
    
    return {
      status: 'passed',
      message: 'PostgreSQL connection successful',
      responseTime: time?.durationMs,
      result: result.rows[0]
    };
  } catch (error) {
    logger.endTimer(timer);
    return {
      status: 'failed',
      message: error.message
    };
  }
}

async function testMongoDB() {
  const timer = logger.startTimer('test:mongodb');
  try {
    const { mongoose } = mongo;
    const adminDb = mongoose.connection.db.admin();
    const result = await adminDb.ping();
    const time = logger.endTimer(timer);
    
    return {
      status: 'passed',
      message: 'MongoDB connection successful',
      responseTime: time?.durationMs,
      result: result
    };
  } catch (error) {
    logger.endTimer(timer);
    return {
      status: 'failed',
      message: error.message
    };
  }
}

async function testRedis() {
  const timer = logger.startTimer('test:redis');
  try {
    const testKey = `test:${Date.now()}`;
    const testValue = { test: true, timestamp: Date.now() };
    
    await redis.set(testKey, testValue, 60);
    const retrieved = await redis.get(testKey);
    await redis.del(testKey);
    
    const time = logger.endTimer(timer);
    
    return {
      status: 'passed',
      message: 'Redis connection successful',
      responseTime: time?.durationMs,
      writeRead: retrieved !== null
    };
  } catch (error) {
    logger.endTimer(timer);
    return {
      status: 'failed',
      message: error.message
    };
  }
}

router.get('/database/crud', testAuth, async (req, res) => {
  const results = {
    timestamp: new Date().toISOString(),
    tests: {}
  };
  
  results.tests.userCRUD = await testUserCRUD();
  results.tests.contentCRUD = await testContentCRUD();
  results.tests.crawlerJobCRUD = await testCrawlerJobCRUD();
  
  const allPassed = Object.values(results.tests).every(t => t.status === 'passed');
  results.overall = allPassed ? 'passed' : 'failed';
  
  res.json({
    success: allPassed,
    data: results
  });
});

async function testUserCRUD() {
  const testId = `test_${Date.now()}`;
  try {
    const user = await User.create({
      username: `test_user_${testId}`,
      email: `test_${testId}@example.com`,
      passwordHash: 'test_hash',
      role: 'user'
    });
    
    const found = await User.findById(user.id);
    if (!found) throw new Error('User not found after create');
    
    await User.delete(user.id);
    
    return { status: 'passed', message: 'User CRUD operations successful', userId: user.id };
  } catch (error) {
    return { status: 'failed', message: error.message };
  }
}

async function testContentCRUD() {
  const testId = `test_${Date.now()}`;
  try {
    const content = await Content.create({
      platformId: 99,
      platformContentId: `test_${testId}`,
      title: 'Test Content',
      content: 'Test content body',
      contentType: 'note'
    });
    
    const found = await Content.findById(content.id);
    if (!found) throw new Error('Content not found after create');
    
    await Content.delete(content.id);
    
    return { status: 'passed', message: 'Content CRUD operations successful', contentId: content.id };
  } catch (error) {
    return { status: 'failed', message: error.message };
  }
}

async function testCrawlerJobCRUD() {
  try {
    const job = await CrawlerJob.create({
      platformId: 99,
      jobType: 'test',
      target: 'test_target',
      maxItems: 1
    });
    
    const found = await CrawlerJob.findById(job.id);
    if (!found) throw new Error('Job not found after create');
    
    await CrawlerJob.delete(job.id);
    
    return { status: 'passed', message: 'CrawlerJob CRUD operations successful', jobId: job.id };
  } catch (error) {
    return { status: 'failed', message: error.message };
  }
}

router.get('/cache', testAuth, async (req, res) => {
  const results = {
    timestamp: new Date().toISOString(),
    tests: {}
  };
  
  const testKey = `test:cache:${Date.now()}`;
  const testValue = { data: 'test', timestamp: Date.now() };
  
  try {
    await redis.set(testKey, testValue, 60);
    results.tests.set = { status: 'passed', message: 'Cache set successful' };
  } catch (error) {
    results.tests.set = { status: 'failed', message: error.message };
  }
  
  try {
    const retrieved = await redis.get(testKey);
    results.tests.get = {
      status: retrieved ? 'passed' : 'failed',
      message: retrieved ? 'Cache get successful' : 'Cache get returned null'
    };
  } catch (error) {
    results.tests.get = { status: 'failed', message: error.message };
  }
  
  try {
    await redis.del(testKey);
    results.tests.del = { status: 'passed', message: 'Cache delete successful' };
  } catch (error) {
    results.tests.del = { status: 'failed', message: error.message };
  }
  
  const allPassed = Object.values(results.tests).every(t => t.status === 'passed');
  results.overall = allPassed ? 'passed' : 'failed';
  
  res.json({
    success: allPassed,
    data: results
  });
});

router.get('/fixtures', testAuth, async (req, res) => {
  const fixtures = {
    users: [
      { username: 'testuser1', email: 'test1@example.com', role: 'user' },
      { username: 'testuser2', email: 'test2@example.com', role: 'user' },
      { username: 'admin', email: 'admin@example.com', role: 'admin' }
    ],
    contents: [
      { platformId: 1, platformContentId: 'test_note_1', title: 'Test Note 1', contentType: 'note' },
      { platformId: 2, platformContentId: 'test_video_1', title: 'Test Video 1', contentType: 'video' }
    ],
    crawlerJobs: [
      { platformId: 1, jobType: 'note', target: 'test_target', maxItems: 10 }
    ]
  };
  
  res.json({
    success: true,
    data: fixtures
  });
});

router.post('/seed', testAuth, async (req, res) => {
  const { count = 10 } = req.body;
  const results = {
    timestamp: new Date().toISOString(),
    created: { users: 0, contents: 0, jobs: 0 },
    errors: []
  };
  
  for (let i = 0; i < count; i++) {
    try {
      await User.create({
        username: `seed_user_${Date.now()}_${i}`,
        email: `seed_${Date.now()}_${i}@test.com`,
        passwordHash: 'seed_hash',
        role: 'user'
      });
      results.created.users++;
    } catch (error) {
      results.errors.push(`User ${i}: ${error.message}`);
    }
    
    try {
      await Content.create({
        platformId: 1,
        platformContentId: `seed_${Date.now()}_${i}`,
        title: `Seed Content ${i}`,
        content: 'Seeded content for testing',
        contentType: 'note'
      });
      results.created.contents++;
    } catch (error) {
      results.errors.push(`Content ${i}: ${error.message}`);
    }
  }
  
  try {
    await CrawlerJob.create({
      platformId: 1,
      jobType: 'seed_test',
      target: 'seed_target',
      maxItems: count
    });
    results.created.jobs++;
  } catch (error) {
    results.errors.push(`Job: ${error.message}`);
  }
  
  res.json({
    success: results.errors.length === 0,
    data: results
  });
});

router.post('/cleanup', testAuth, async (req, res) => {
  const results = {
    timestamp: new Date().toISOString(),
    deleted: { users: 0, contents: 0, jobs: 0, analysis: 0 }
  };
  
  try {
    const userResult = await pg.query(
      "DELETE FROM users WHERE username LIKE 'test_%' OR username LIKE 'seed_%'"
    );
    results.deleted.users = userResult.rowCount;
  } catch (error) {
    logger.error('Cleanup users failed', { error: error.message });
  }
  
  try {
    const contentResult = await pg.query(
      "DELETE FROM contents WHERE platform_content_id LIKE 'test_%' OR platform_content_id LIKE 'seed_%'"
    );
    results.deleted.contents = contentResult.rowCount;
  } catch (error) {
    logger.error('Cleanup contents failed', { error: error.message });
  }
  
  try {
    const jobResult = await pg.query(
      "DELETE FROM crawler_jobs WHERE target LIKE 'test_%' OR target LIKE 'seed_%'"
    );
    results.deleted.jobs = jobResult.rowCount;
  } catch (error) {
    logger.error('Cleanup jobs failed', { error: error.message });
  }
  
  try {
    const analysisResult = await pg.query(
      "DELETE FROM analysis_results WHERE content_id IN (SELECT id FROM contents WHERE platform_content_id LIKE 'test_%')"
    );
    results.deleted.analysis = analysisResult.rowCount;
  } catch (error) {
    logger.error('Cleanup analysis failed', { error: error.message });
  }
  
  res.json({
    success: true,
    data: results
  });
});

router.get('/mock/:type', testAuth, (req, res) => {
  const { type } = req.params;
  const { count = 1 } = req.query;
  
  const mocks = {
    user: () => ({
      username: `mock_user_${Date.now()}`,
      email: `mock_${Date.now()}@example.com`,
      role: 'user'
    }),
    content: () => ({
      platformId: Math.floor(Math.random() * 3) + 1,
      platformContentId: `mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      title: `Mock Content ${Date.now()}`,
      content: 'This is mock content for testing purposes.',
      contentType: ['note', 'video'][Math.floor(Math.random() * 2)],
      likeCount: Math.floor(Math.random() * 10000),
      commentCount: Math.floor(Math.random() * 1000)
    }),
    crawlerJob: () => ({
      platformId: Math.floor(Math.random() * 3) + 1,
      jobType: ['video', 'user', 'search'][Math.floor(Math.random() * 3)],
      target: 'mock_target',
      maxItems: Math.floor(Math.random() * 100) + 10
    }),
    analysis: () => ({
      sentimentScore: Math.random() * 2 - 1,
      sentimentLabel: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)],
      sentimentConfidence: Math.random() * 0.5 + 0.5,
      qualityScore: Math.random() * 0.5 + 0.5,
      viralScore: Math.random()
    })
  };
  
  if (!mocks[type]) {
    return res.status(400).json({
      success: false,
      error: `Unknown mock type: ${type}. Available: ${Object.keys(mocks).join(', ')}`
    });
  }
  
  const items = [];
  for (let i = 0; i < parseInt(count); i++) {
    items.push(mocks[type]());
  }
  
  res.json({
    success: true,
    data: {
      type,
      count: items.length,
      items
    }
  });
});

module.exports = router;
