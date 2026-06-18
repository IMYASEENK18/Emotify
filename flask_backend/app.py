 
"""
Emotify Flask Backend - Main API
Handles emotion detection requests from Express backend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import os

from config import FLASK_HOST, FLASK_PORT, DEBUG, CORS_ORIGINS, MAX_IMAGE_SIZE, ALLOWED_EXTENSIONS
from utils.face_detector import FaceDetector
from utils.emotion_predictor import EmotionPredictor

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)

# Initialize detectors (will be loaded on first request to save startup time)
face_detector = None
emotion_predictor = None


def init_models():
    """Initialize models on first request"""
    global face_detector, emotion_predictor
    
    if face_detector is None:
        print("🔧 Initializing face detector...")
        face_detector = FaceDetector()
    
    if emotion_predictor is None:
        print("🔧 Initializing emotion predictor...")
        emotion_predictor = EmotionPredictor()


def decode_base64_image(base64_string):
    """
    Decode base64 image to OpenCV format
    
    Args:
        base64_string: Base64 encoded image (with or without data URI prefix)
    
    Returns:
        numpy array (BGR format) or None
    """
    try:
        # Remove data URI prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        image = Image.open(BytesIO(image_data))
        
        # Convert to numpy array
        image_np = np.array(image)
        
        # Convert to BGR for OpenCV
        if len(image_np.shape) == 2:  # Grayscale
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        elif image_np.shape[2] == 4:  # RGBA
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
        elif image_np.shape[2] == 3:  # RGB
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        return image_np
    
    except Exception as e:
        print(f"❌ Error decoding image: {e}")
        return None


@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'Emotify Flask Backend',
        'version': '1.0.0',
        'endpoints': {
            'detect': '/api/detect (POST)',
            'health': '/api/health (GET)',
            'test': '/api/test (GET)'
        }
    }), 200


@app.route('/api/health', methods=['GET'])
def health():
    """Health check with model status"""
    init_models()
    
    return jsonify({
        'status': 'healthy',
        'face_detector': face_detector is not None,
        'emotion_predictor': emotion_predictor is not None and emotion_predictor.model is not None
    }), 200


@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint - no image required"""
    init_models()
    
    return jsonify({
        'status': 'success',
        'message': 'Flask backend is working!',
        'face_detector_ready': face_detector is not None,
        'emotion_model_ready': emotion_predictor is not None and emotion_predictor.model is not None
    }), 200


@app.route('/api/detect', methods=['POST'])
def detect_emotion():
    """
    Main emotion detection endpoint
    
    Expected JSON:
    {
        "image": "base64_encoded_image_string"
    }
    
    Returns:
    {
        "success": true,
        "emotion": "happy",
        "confidence": 0.87,
        "probabilities": {
            "angry": 0.02,
            "disgust": 0.01,
            ...
        },
        "face_detected": true
    }
    """
    # Initialize models
    init_models()
    
    # Check if models are loaded
    if face_detector is None:
        return jsonify({
            'success': False,
            'error': 'Face detector not initialized'
        }), 500
    
    if emotion_predictor is None or emotion_predictor.model is None:
        return jsonify({
            'success': False,
            'error': 'Emotion model not loaded. Please add emotion_model.h5 to models/ folder'
        }), 500
    
    # Get JSON data
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided. Send base64 image in "image" field'
            }), 400
        
        base64_image = data['image']
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Invalid JSON data: {str(e)}'
        }), 400
    
    # Decode image
    image = decode_base64_image(base64_image)
    
    if image is None:
        return jsonify({
            'success': False,
            'error': 'Failed to decode image'
        }), 400
    
    # Detect face
    try:
        face_crop = face_detector.get_largest_face(image)
        
        if face_crop is None:
            return jsonify({
                'success': False,
                'error': 'No face detected in image',
                'face_detected': False
            }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Face detection failed: {str(e)}'
        }), 500
    
    # Predict emotion
    try:
        prediction = emotion_predictor.predict_emotion(face_crop)
        
        if 'error' in prediction:
            return jsonify({
                'success': False,
                'error': f'Emotion prediction failed: {prediction["error"]}'
            }), 500
        
        return jsonify({
            'success': True,
            'emotion': prediction['emotion'],
            'confidence': round(prediction['confidence'], 4),
            'probabilities': {k: round(v, 4) for k, v in prediction['probabilities'].items()},
            'face_detected': True
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Emotion prediction failed: {str(e)}'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 EMOTIFY FLASK BACKEND")
    print("="*60)
    print(f"📍 Host: {FLASK_HOST}")
    print(f"📍 Port: {FLASK_PORT}")
    print(f"🔧 Debug: {DEBUG}")
    print("="*60 + "\n")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=DEBUG
    )