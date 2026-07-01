const express = require('express');
const router = express.Router();
const path = require('path');
const Session = require('../models/session');
const User = require('../models/user');
const axios = require('axios');

// ── MIDDLEWARE: check auth ──
function requireAuth(req, res, next) {
  if (req.session.userId) return next();
  res.redirect('/');
}

// ── DEBUG ROUTE ──
router.get('/api/debug-session', (req, res) => {
  res.json({
    sessionId: req.session.id,
    userId: req.session.userId,
    hasToken: !!req.session.spotifyToken,
    token: req.session.spotifyToken || 'MISSING'
  });
});

// ── PAGE ROUTES ──

router.get('/', (req, res) => {
  if (req.session.userId) return res.redirect('/welcome');
  res.sendFile(path.join(__dirname, '../views/login.html'));
});
router.get('/welcome', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/welcome.html'));
});

router.get('/region', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/region.html'));
});

router.get('/detect', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/detect.html'));
});

router.get('/music', requireAuth, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/music.html'));
});

// ── API: Get session user info ──
router.get('/api/me', requireAuth, async (req, res) => {
  try {
    const user = await User.findById(req.session.userId);
    res.json({
      name: user.name,
      isTrial: user.isTrial,
      trialValid: user.isTrialValid(),
       trialStart: user.trialStartDate,
      region: user.region
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── API: Save region ──
router.post('/api/region', requireAuth, async (req, res) => {
  try {
    const { region } = req.body;
    await User.findByIdAndUpdate(req.session.userId, { region });
    req.session.region = region;
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── API: Save emotion session ──
router.post('/api/session', requireAuth, async (req, res) => {
  try {
    const { emotion, confidence, region, songs } = req.body;
    const session = new Session({
      userId: req.session.userId,
      emotion, confidence, region, songs
    });
    await session.save();
    req.session.emotion = emotion;
    req.session.confidence = confidence;
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── API: Get Spotify recommendations ──
router.get('/api/spotify/recommendations', requireAuth, async (req, res) => {
  try {
    const { emotion, region } = req.query;
    const token = req.session.spotifyToken;

    console.log('Token in recommendations:', token ? 'EXISTS' : 'MISSING');

    if (!token) {
      return res.json({ spotify: false });
    }

    // Enhanced emotion queries with region-specific genres
    const getEmotionQuery = (emotion, region) => {
      const baseQueries = {
        happy: 'happy upbeat feel good',
        sad: 'sad emotional heartbreak',
        angry: 'angry rock intense',
        fearful: 'dark ambient mysterious',
        disgusted: 'alternative indie melancholic',
        surprised: 'energetic electronic pop',
        neutral: 'chill lofi relaxing'
      };

      const regionGenres = {
        'PK': ' pakistani sufi qawwali',
        'IN': ' bollywood hindi',
        'US': ' pop rock',
        'GB': ' british indie',
        'SA': ' arabic khaleeji',
        'TR': ' turkish pop',
        'JP': ' jpop',
        'KR': ' kpop',
        'BR': ' bossa nova samba',
        'MX': ' latin reggaeton'
      };

      const base = baseQueries[emotion] || 'chill';
      const regionExtra = regionGenres[region] || '';
      
      return base + regionExtra;
    };

    // Market code mapping for Spotify API
    const marketMap = {
      'PK': 'PK',    // Pakistan
      'IN': 'IN',    // India
      'US': 'US',    // United States
      'GB': 'GB',    // United Kingdom
      'SA': 'SA',    // Saudi Arabia
      'TR': 'TR',    // Turkey
      'JP': 'JP',    // Japan
      'KR': 'KR',    // South Korea
      'AE': 'AE',    // UAE
      'CA': 'CA',    // Canada
      'AU': 'AU',    // Australia
      'DE': 'DE',    // Germany
      'FR': 'FR',    // France
      'ES': 'ES',    // Spain
      'BR': 'BR',    // Brazil
      'MX': 'MX',    // Mexico
      'AR': 'AR'     // Argentina
    };

    const market = marketMap[region] || 'US';
    const query = getEmotionQuery(emotion, region);

    const response = await axios.get('https://api.spotify.com/v1/search', {
      headers: { Authorization: `Bearer ${token}` },
      params: {
        q: query,
        type: 'track',
        limit: 6,
        market: market
      }
    });

    const tracks = response.data.tracks.items.map(t => ({
      name: t.name,
      artist: t.artists.map(a => a.name).join(', '),
      album: t.album.name,
      image: t.album.images[0]?.url,
      preview: t.preview_url,
      url: t.external_urls.spotify,
      trackId: t.id
    }));

    res.json({ spotify: true, tracks });

  } catch (err) {
    console.error('Spotify API error:', err.message);
    res.json({ spotify: false });
  }
});

// ── API: Get YouTube recommendations (for free trial users) ──
router.get('/api/youtube/recommendations', requireAuth, async (req, res) => {
  try {
    const { emotion, region } = req.query;

    const emotionQueries = {
      happy: 'happy upbeat music',
      sad: 'sad emotional music',
      angry: 'angry rock music',
      fearful: 'dark ambient music',
      disgusted: 'alternative indie music',
      surprised: 'energetic pop music',
      neutral: 'chill lofi music'
    };

    const regionGenres = {
      'PK': ' pakistani sufi',
      'IN': ' bollywood',
      'US': ' pop',
      'GB': ' indie',
      'SA': ' arabic',
      'TR': ' turkish',
      'JP': ' jpop',
      'KR': ' kpop',
      'BR': ' brazilian',
      'MX': ' latin'
    };

    const query = (emotionQueries[emotion] || 'music') + (regionGenres[region] || '');

    const response = await axios.get('https://www.googleapis.com/youtube/v3/search', {
      params: {
        part: 'snippet',
        q: query,
        type: 'video',
        videoCategoryId: '10',
        maxResults: 6,
        key: process.env.YOUTUBE_API_KEY
      }
    });

    const videos = response.data.items.map(item => ({
      videoId: item.id.videoId,
      title: item.snippet.title,
      artist: item.snippet.channelTitle,
      thumbnail: item.snippet.thumbnails.medium.url,
      url: `https://www.youtube.com/watch?v=${item.id.videoId}`
    }));

    res.json({ youtube: true, videos });

  } catch (err) {
    console.error('YouTube API error:', err.message);
    res.json({ youtube: false });
  }
});

module.exports = router;