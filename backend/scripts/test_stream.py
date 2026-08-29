import os
import sys
import numpy as np
import cv2

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.safety import processor

def main():
    os.environ["TESTING"] = "true"
    client = TestClient(app)
    
    print("=" * 60)
    print("SiteGuard AI - Step 10 Live MJPEG Stream Integration Test")
    print("=" * 60)
    
    # 1. Inject a mock frame into the processor memory
    print("[*] Simulating frame generation in processor...")
    mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(mock_frame, "SITEGUARD AI LIVE TESTING", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    processor.LATEST_FRAME = mock_frame
    
    # 2. Call the stream endpoint
    print("[*] Requesting live video stream (GET /api/v1/stream)...")
    
    # We use streaming = True under httpx client (accessed via client.stream) to read chunks
    # without hanging on the infinite stream.
    with client.stream("GET", "/api/v1/stream") as response:
        print(f"  - Status Code: {response.status_code}")
        print(f"  - Content-Type: {response.headers.get('content-type')}")
        
        assert response.status_code == 200
        assert "multipart/x-mixed-replace" in response.headers.get("content-type", "")
        
        # Read the first few chunks of the MJPEG stream to confirm format
        chunk_count = 0
        for chunk in response.iter_bytes():
            if b"--frame" in chunk:
                print("  - Verified: Stream boundary '--frame' detected in chunk data.")
                break
            chunk_count += 1
            if chunk_count > 10:
                raise AssertionError("Did not find boundary in stream chunks.")
                
    print("=" * 60)
    print("SiteGuard AI - Step 10 live video stream: SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    main()
