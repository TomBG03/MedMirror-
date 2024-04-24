const mongoose = require('mongoose');

const FeatureUsageSchema = new mongoose.Schema({
  featureName: {
    type: String,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  }
});

const FeatureUsage = mongoose.model('FeatureUsage', FeatureUsageSchema);
module.exports = FeatureUsage;