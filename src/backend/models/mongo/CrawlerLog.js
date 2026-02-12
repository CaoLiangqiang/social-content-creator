const { mongoose } = require('../config/mongodb');

const crawlerLogSchema = new mongoose.Schema({
  taskId: {
    type: String,
    required: true,
    index: true
  },
  platform: {
    type: String,
    required: true
  },
  level: {
    type: String,
    enum: ['info', 'warning', 'error', 'debug'],
    default: 'info'
  },
  message: {
    type: String,
    required: true
  },
  details: {
    type: mongoose.Schema.Types.Mixed
  },
  performanceMetrics: {
    duration: Number,
    memoryUsage: Number,
    successRate: Number
  }
}, {
  timestamps: true,
  collection: 'crawler_logs'
});

crawlerLogSchema.index({ taskId: 1, createdAt: -1 });
crawlerLogSchema.index({ platform: 1, level: 1 });
crawlerLogSchema.index({ createdAt: -1 });

crawlerLogSchema.statics.getTaskLogs = async function(taskId, options = {}) {
  const { level, limit = 100 } = options;
  const query = { taskId };
  
  if (level) {
    query.level = level;
  }
  
  return this.find(query)
    .sort({ createdAt: -1 })
    .limit(limit);
};

crawlerLogSchema.statics.getErrorCount = async function(taskId) {
  return this.countDocuments({ taskId, level: 'error' });
};

const CrawlerLog = mongoose.model('CrawlerLog', crawlerLogSchema);

module.exports = CrawlerLog;
