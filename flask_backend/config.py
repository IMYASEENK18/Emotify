 
"""
Configuration file for Emotify Flask Backend
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Model configuration
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'emotion_model.h5')
IMG_SIZE = 48  # FER2013 standard size
EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

# Face detection configuration
FACE_CASCADE_PATH = 'haarcascade_frontalface_default.xml'
MIN_FACE_SIZE = (30, 30)
SCALE_FACTOR = 1.1
MIN_NEIGHBORS = 5

# Flask configuration
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000
DEBUG = True

# CORS settings
CORS_ORIGINS = ['http://127.0.0.1:3000', 'http://localhost:3000']

# API settings
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}