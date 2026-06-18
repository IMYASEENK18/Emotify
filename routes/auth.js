require('dotenv').config();
const express = require('express');
const router = express.Router();
const User = require('../models/user');
const axios = require('axios');
const bcrypt = require('bcryptjs');
// ── SPOTIFY AUTH ──
router.get('/spotify', (req, res) => {
  const scopes = [
    'user-read-private',
    'user-read-email',
    'playlist-read-private',
    'streaming',
    'user-top-read'
  ].join(' ');

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: process.env.SPOTIFY_CLIENT_ID,
    scope: scopes,
    redirect_uri: process.env.SPOTIFY_REDIRECT_URI
  });

  res.redirect(`https://accounts.spotify.com/authorize?${params}`);
});

// ── SPOTIFY CALLBACK ──
router.get('/spotify/callback', async (req, res) => {
  const { code } = req.query;
  try {
    const tokenRes = await axios.post(
      'https://accounts.spotify.com/api/token',
      new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: process.env.SPOTIFY_REDIRECT_URI,
        client_id: process.env.SPOTIFY_CLIENT_ID,
        client_secret: process.env.SPOTIFY_CLIENT_SECRET
      }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );

    const { access_token, refresh_token } = tokenRes.data;

    const profileRes = await axios.get('https://api.spotify.com/v1/me', {
      headers: { Authorization: `Bearer ${access_token}` }
    });

    const { id, display_name, email } = profileRes.data;

    let user = await User.findOne({ spotifyId: id });
    if (!user) {
      user = new User({
        name: display_name || 'Music Lover',
        email: email,
        spotifyId: id,
        spotifyAccessToken: access_token,
        spotifyRefreshToken: refresh_token,
        isTrial: false
      });
      await user.save();
    } else {
      user.spotifyAccessToken = access_token;
      user.spotifyRefreshToken = refresh_token;
      await user.save();
    }

    req.session.userId = user._id;
    req.session.userName = user.name;
    req.session.isTrial = false;
    req.session.spotifyToken = access_token;

    console.log('SAVING TOKEN:', access_token);
    console.log('SESSION BEFORE SAVE:', req.session);

    req.session.save((err) => {
      if (err) console.error('Session save error:', err);
      res.redirect('/welcome');
    });

  } catch (err) {
    console.error('Spotify auth error:', err.message);
    res.redirect('/?error=spotify_failed');
  }
});

// ── FREE TRIAL ──
router.post('/trial', async (req, res) => {
  try {
    const { name } = req.body;

    // If user with same name exists, log them back in
    let trialUser = await User.findOne({ name: name, isTrial: true });
    if (!trialUser) {
      trialUser = new User({
        name: name || 'Explorer',
        isTrial: true,
        trialStartDate: new Date()
      });
      await trialUser.save();
    }

    req.session.userId = trialUser._id;
    req.session.userName = trialUser.name;
    req.session.isTrial = true;

    return res.json({ success: true, name: trialUser.name });
  } catch (err) {
    console.error('Trial error:', err);
    return res.status(500).json({ success: false, error: err.message });
  }
});

// ── LOGOUT ──
router.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});
// ── REGISTER ──
router.post('/register', async (req, res) => {
  try {
    const { name, email, password } = req.body;
    const existing = await User.findOne({ email });
    if (existing) return res.json({ success: false, error: 'Email already registered. Please sign in.' });
    const user = new User({ name, email, password, isTrial: true, trialStartDate: new Date() });
    await user.save();
    req.session.userId = user._id;
    req.session.userName = user.name;
    req.session.isTrial = true;
    return res.json({ success: true });
  } catch (err) {
    return res.status(500).json({ success: false, error: err.message });
  }
});

// ── SIGN IN ──
router.post('/signin', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.json({ success: false, error: 'No account found with this email.' });
    if (!user.password) return res.json({ success: false, error: 'Please use Spotify to sign in.' });
    const match = await bcrypt.compare(password, user.password);
    if (!match) return res.json({ success: false, error: 'Incorrect password.' });
    req.session.userId = user._id;
    req.session.userName = user.name;
    req.session.isTrial = true;
    return res.json({ success: true });
  } catch (err) {
    return res.status(500).json({ success: false, error: err.message });
  }
});
module.exports = router;