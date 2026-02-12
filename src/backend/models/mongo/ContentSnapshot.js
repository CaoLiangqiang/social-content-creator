const { mongoose } = require('../config/mongodb');

const contentSnapshotSchema = new mongoose.Schema({
  contentId: {
    type: String,
    required: true,
    index: true
  },
  platform: {
    type: String,
    required: true
  },
  platformContentId: {
    type: String,
    required: true,
    index: true
  },
  snapshotData: {
    viewCount: Number,
    likeCount: Number,
    commentCount: Number,
    shareCount: Number,
    collectCount: Number
  },
  snapshotTime: {
    type: Date,
    default: Date.now,
    index: true
  }
}, {
  timestamps: true,
  collection: 'content_snapshots'
});

contentSnapshotSchema.index({ contentId: 1, snapshotTime: -1 });
contentSnapshotSchema.index({ platformContentId: 1, snapshotTime: -1 });

contentSnapshotSchema.statics.getLatestSnapshot = async function(contentId) {
  return this.findOne({ contentId }).sort({ snapshotTime: -1 });
};

contentSnapshotSchema.statics.getSnapshotHistory = async function(contentId, days = 7) {
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  return this.find({
    contentId,
    snapshotTime: { $gte: startDate }
  }).sort({ snapshotTime: 1 });
};

const ContentSnapshot = mongoose.model('ContentSnapshot', contentSnapshotSchema);

module.exports = ContentSnapshot;
