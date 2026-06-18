const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const UserSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, unique: true, sparse: true },
  spotifyId: { type: String, unique: true, sparse: true },
  spotifyAccessToken: String,
  spotifyRefreshToken: String,
  isTrial: { type: Boolean, default: false },
  trialStartDate: { type: Date, default: Date.now },
  region: { type: String, default: 'PK' },
  password: { type: String },
  createdAt: { type: Date, default: Date.now }
});

UserSchema.pre('save', async function() {
  if (!this.isModified('password') || !this.password) return;
  this.password = await bcrypt.hash(this.password, 10);
});

UserSchema.methods.isTrialValid = function() {
  const now = new Date();
  const diff = (now - this.trialStartDate) / (1000 * 60 * 60 * 24);
  return diff <= 7;
};

module.exports = mongoose.model('User', UserSchema);