 
"""
Emotion Prediction using trained MobileNetV2 model
"""
import numpy as np
import cv2
from tensorflow import keras
from config import MODEL_PATH, IMG_SIZE, EMOTIONS


class EmotionPredictor:
    """Predict emotions from face images"""
    
    def __init__(self, model_path=None):
        """
        Initialize the emotion predictor
        
        Args:
            model_path: Path to the trained model (.h5 or .keras file)
        """
        self.model_path = model_path or MODEL_PATH
        self.img_size = IMG_SIZE
        self.emotions = EMOTIONS
        self.model = None
        
        self.load_model()
    
    def load_model(self):
        """Load the trained emotion recognition model"""
        try:
            print(f"📦 Loading model from: {self.model_path}")
            self.model = keras.models.load_model(self.model_path)
            print("✅ Model loaded successfully")
            print(f"   Input shape: {self.model.input_shape}")
            print(f"   Output shape: {self.model.output_shape}")
        except FileNotFoundError:
            print(f"❌ Model file not found: {self.model_path}")
            print("⚠️  Please place your trained model in the 'models/' folder")
            self.model = None
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
    
    def preprocess_face(self, face_image):
        """
        Preprocess face image for model input
        
        Args:
            face_image: numpy array (BGR format)
        
        Returns:
            Preprocessed image ready for model
        """
        # Convert to grayscale
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        # Resize to model input size
        resized = cv2.resize(gray, (self.img_size, self.img_size))
        
        # Normalize pixel values
        normalized = resized / 255.0
        
        # Add batch and channel dimensions: (1, 48, 48, 1)
        preprocessed = np.expand_dims(normalized, axis=-1)
        preprocessed = np.expand_dims(preprocessed, axis=0)
        
        return preprocessed
    
    def predict_emotion(self, face_image):
        """
        Predict emotion from a face image
        
        Args:
            face_image: numpy array (BGR format)
        
        Returns:
            dict: {
                'emotion': str,
                'confidence': float,
                'probabilities': dict
            }
        """
        if self.model is None:
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'probabilities': {},
                'error': 'Model not loaded'
            }
        
        try:
            # Preprocess
            preprocessed = self.preprocess_face(face_image)
            
            # Predict
            predictions = self.model.predict(preprocessed, verbose=0)
            probabilities = predictions[0]
            
            # Get top prediction
            emotion_idx = np.argmax(probabilities)
            emotion = self.emotions[emotion_idx]
            confidence = float(probabilities[emotion_idx])
            
            # Create probabilities dict
            prob_dict = {
                self.emotions[i]: float(probabilities[i])
                for i in range(len(self.emotions))
            }
            
            return {
                'emotion': emotion,
                'confidence': confidence,
                'probabilities': prob_dict
            }
        
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'probabilities': {},
                'error': str(e)
            }
    
    def predict_from_base64(self, base64_string):
        """
        Predict emotion from base64 encoded image
        
        Args:
            base64_string: Base64 encoded image
        
        Returns:
            Prediction result dict
        """
        import base64
        from io import BytesIO
        from PIL import Image
        
        try:
            # Decode base64
            image_data = base64.b64decode(base64_string.split(',')[1] if ',' in base64_string else base64_string)
            image = Image.open(BytesIO(image_data))
            
            # Convert to OpenCV format
            image_np = np.array(image)
            if len(image_np.shape) == 2:  # Grayscale
                image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
            elif image_np.shape[2] == 4:  # RGBA
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
            elif image_np.shape[2] == 3:  # RGB
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            return self.predict_emotion(image_np)
        
        except Exception as e:
            print(f"❌ Base64 decoding error: {e}")
            return {
                'emotion': 'neutral',
                'confidence': 0.0,
                'probabilities': {},
                'error': str(e)
            }