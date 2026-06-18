const mongoose = require('mongoose');

const SessionSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  emotion: String,
  confidence: Number,
  region: String,
  songs: Array,
  detectedAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Session', SessionSchema);