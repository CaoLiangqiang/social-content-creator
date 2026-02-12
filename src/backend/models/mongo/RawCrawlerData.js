const { mongoose } = require('../config/mongodb');

const rawCrawlerDataSchema = new mongoose.Schema({
  platform: {
    type: String,
    required: true,
    enum: ['xiaohongshu', 'bilibili', 'douyin', 'weibo', 'zhihu']
  },
  dataType: {
    type: String,
    required: true,
    enum: ['note', 'video', 'user', 'comment', 'danmaku']
  },
  platformContentId: {
    type: String,
    required: true,
    index: true
  },
  rawHtml: {
    type: String
  },
  rawJson: {
    type: mongoose.Schema.Types.Mixed
  },
  metadata: {
    url: String,
    crawledAt: {
      type: Date,
      default: Date.now
    },
    crawlerVersion: String,
    userAgent: String,
    proxyUsed: String
  },
  processed: {
    type: Boolean,
    default: false
  },
  processedAt: Date,
  contentId: {
    type: String,
    ref: 'Content'
  }
}, {
  timestamps: true,
  collection: 'raw_crawler_data'
});

rawCrawlerDataSchema.index({ platform: 1, dataType: 1 });
rawCrawlerDataSchema.index({ processed: 1 });
rawCrawlerDataSchema.index({ createdAt: -1 });
rawCrawlerDataSchema.index({ platform: 1, platformContentId: 1 }, { unique: true });

const RawCrawlerData = mongoose.model('RawCrawlerData', rawCrawlerDataSchema);

module.exports = RawCrawlerData;
