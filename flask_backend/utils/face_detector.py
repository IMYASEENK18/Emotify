 
"""
Face Detection using OpenCV Haar Cascades
"""
import cv2
import numpy as np
from config import FACE_CASCADE_PATH, MIN_FACE_SIZE, SCALE_FACTOR, MIN_NEIGHBORS


class FaceDetector:
    """Detect faces in images using OpenCV"""
    
    def __init__(self):
        """Initialize the face detector"""
        try:
            # Try to load Haar Cascade from OpenCV installation
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            if self.face_cascade.empty():
                raise Exception("Failed to load Haar Cascade")
            
            print("✅ Face detector initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing face detector: {e}")
            raise
    
    def detect_faces(self, image):
        """
        Detect faces in an image
        
        Args:
            image: numpy array (BGR format from cv2)
        
        Returns:
            List of face coordinates [(x, y, w, h), ...]
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=SCALE_FACTOR,
            minNeighbors=MIN_NEIGHBORS,
            minSize=MIN_FACE_SIZE
        )
        
        return faces
    
    def get_largest_face(self, image):
        """
        Get the largest face in the image
        
        Args:
            image: numpy array (BGR format)
        
        Returns:
            Face crop (numpy array) or None if no face found
        """
        faces = self.detect_faces(image)
        
        if len(faces) == 0:
            return None
        
        # Get largest face by area
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face
        
        # Extract face region
        face_crop = image[y:y+h, x:x+w]
        
        return face_crop
    
    def draw_faces(self, image, faces):
        """
        Draw rectangles around detected faces
        
        Args:
            image: numpy array
            faces: List of face coordinates
        
        Returns:
            Image with rectangles drawn
        """
        output = image.copy()
        
        for (x, y, w, h) in faces:
            cv2.rectangle(output, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        return output