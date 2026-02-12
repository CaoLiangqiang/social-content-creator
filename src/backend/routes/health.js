const express = require('express');
const router = express.Router();
const { healthCheck } = require('../config');

router.get('/', async (req, res) => {
  res.json({
    success: true,
    data: {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: '0.4.0'
    }
  });
});

router.get('/db', async (req, res) => {
  try {
    const health = await healthCheck();
    res.json({
      success: true,
      data: health
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/ready', async (req, res) => {
  try {
    const health = await healthCheck();
    
    if (health.status === 'healthy') {
      res.json({
        success: true,
        message: 'Service is ready'
      });
    } else {
      res.status(503).json({
        success: false,
        message: 'Service is not ready',
        services: health.services
      });
    }
  } catch (error) {
    res.status(503).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/live', (req, res) => {
  res.json({
    success: true,
    message: 'Service is alive'
  });
});

module.exports = router;
