 
"""
Test script for Emotify Flask Backend
"""
import requests
import json
import base64
import cv2


def test_health():
    """Test health endpoint"""
    print("\n🧪 Testing /api/health...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/health')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_with_webcam():
    """Test emotion detection with webcam image"""
    print("\n🧪 Testing /api/detect with webcam...")
    
    # Capture image from webcam
    print("📸 Capturing image from webcam...")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Failed to capture image from webcam")
        return False
    
    # Convert to base64
    _, buffer = cv2.imencode('.jpg', frame)
    base64_image = base64.b64encode(buffer).decode('utf-8')
    
    # Send request
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/detect',
            json={'image': base64_image},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"\n✅ Detected emotion: {result['emotion']}")
            print(f"✅ Confidence: {result['confidence']*100:.2f}%")
        
        return result.get('success', False)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_without_image():
    """Test API with no image (should fail gracefully)"""
    print("\n🧪 Testing /api/detect without image...")
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/detect',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 400
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    print("="*60)
    print("🧪 EMOTIFY FLASK BACKEND - TEST SUITE")
    print("="*60)
    
    print("\n⚠️  Make sure Flask backend is running!")
    print("   Run: python app.py\n")
    
    input("Press Enter to start tests...")
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health()))
    results.append(("No Image Error", test_without_image()))
    results.append(("Webcam Detection", test_with_webcam()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nPassed: {passed}/{total}")
    print("="*60)