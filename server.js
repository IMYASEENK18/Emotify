require('dotenv').config();
const express = require('express');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const cors = require('cors');
const path = require('path');
const connectDB = require('./config/db');

const app = express();

// Connect to MongoDB
connectDB();

// Middlewares
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cors({
  origin: 'http://127.0.0.1:3000',
  credentials: true
}));

// Content Security Policy middleware
app.use((req, res, next) => {
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.spotify.com https://sdk.scdn.co https://www.youtube.com https://www.googleapis.com https://cdn.jsdelivr.net; " +
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
    "font-src 'self' https://fonts.gstatic.com; " +
    "img-src 'self' data: https://*; " +
    "frame-src 'self' https://open.spotify.com https://www.youtube.com; " +
    "connect-src 'self' https://api.spotify.com https://accounts.spotify.com https://www.googleapis.com;"
  );
  next();
});
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: true,
  saveUninitialized: true,
  cookie: { 
    maxAge: 7 * 24 * 60 * 60 * 1000,
    httpOnly: true,
    secure: false,
    sameSite: 'lax'
  }
}));
app.use(cookieParser());

// Serve HTML files from views folder
app.use(express.static(path.join(__dirname, 'views')));

// Routes
const authRoutes = require('./routes/auth');
const appRoutes = require('./routes/app');

app.use('/auth', authRoutes);
app.use('/', appRoutes);

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✅ Emotify running at http://127.0.0.1:${PORT}`);
});
