import os
import sys
import json
from fastapi.testclient import TestClient

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

def main():
    client = TestClient(app)
    
    print("=" * 60)
    print("SiteGuard AI - Step 8 REST API Integration Test")
    print("=" * 60)
    
    # 1. Test Root Endpoint
    print("[*] Testing Root endpoint (GET /)...")
    res_root = client.get("/")
    print(f"  - Status Code: {res_root.status_code}")
    print(f"  - Response: {res_root.json()}")
    assert res_root.status_code == 200
    
    # 2. Test Health Endpoint
    print("\n[*] Testing Health endpoint (GET /health)...")
    res_health = client.get("/health")
    print(f"  - Status Code: {res_health.status_code}")
    print(f"  - Response: {res_health.json()}")
    assert res_health.status_code == 200
    
    # 3. Test Zones Configuration Endpoint
    print("\n[*] Testing Zones configuration endpoint (GET /api/v1/zones)...")
    res_zones = client.get("/api/v1/zones")
    print(f"  - Status Code: {res_zones.status_code}")
    print(f"  - Safety Zones Configured: {len(res_zones.json()['zones'])}")
    for zone in res_zones.json()['zones']:
         print(f"    * {zone['name']} ({zone['zone_type']}): Coordinates count: {len(zone['coordinates'])}")
    assert res_zones.status_code == 200
    
    # 4. Test Events Retrieval Endpoint (from the Step 7 run)
    print("\n[*] Testing Events retrieval endpoint (GET /api/v1/events)...")
    res_events = client.get("/api/v1/events")
    print(f"  - Status Code: {res_events.status_code}")
    events_count = len(res_events.json())
    print(f"  - Events Found: {events_count}")
    if events_count > 0:
        print("  - Sample Event Struct:")
        print(json.dumps(res_events.json()[0], indent=4))
    assert res_events.status_code == 200
    
    # 5. Test Compliance Stats Endpoint
    print("\n[*] Testing Compliance Stats endpoint (GET /api/v1/stats)...")
    res_stats = client.get("/api/v1/stats")
    print(f"  - Status Code: {res_stats.status_code}")
    print("  - Response Stats Summary:")
    print(json.dumps(res_stats.json(), indent=4))
    assert res_stats.status_code == 200
    
    # 6. Test Recording Upload Endpoint (Validation check only)
    print("\n[*] Testing Recording Upload Validation (POST /api/v1/recordings/upload)...")
    mock_file_data = b"dummy video content"
    files = {"file": ("test_upload.mp4", mock_file_data, "video/mp4")}
    
    from unittest.mock import patch
    with patch("app.main.process_video") as mock_proc:
        res_upload = client.post("/api/v1/recordings/upload", files=files)
        print(f"  - Status Code: {res_upload.status_code}")
        print(f"  - Response: {res_upload.json()}")
        assert res_upload.status_code == 200
        mock_proc.assert_called_once()
        print("  - Verified: Background processing task was successfully scheduled.")
    
    print("=" * 60)
    print("SiteGuard AI - REST API Integration Test: SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    main()
