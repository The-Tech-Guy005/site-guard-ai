import os
import sys
import csv
import io

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app

def main():
    client = TestClient(app)
    
    print("=" * 60)
    print("SiteGuard AI - Step 9 Safety Report Export Integration Test")
    print("=" * 60)
    
    # 1. Test Full CSV Export
    print("[*] Fetching complete safety compliance audit report (GET /api/v1/reports/export)...")
    response = client.get("/api/v1/reports/export")
    
    print(f"  - Status Code: {response.status_code}")
    print(f"  - Content-Type: {response.headers.get('content-type')}")
    print(f"  - Content-Disposition: {response.headers.get('content-disposition')}")
    
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "osha_compliance_report.csv" in response.headers.get("content-disposition", "")
    
    # Parse CSV contents
    csv_content = response.text
    f = io.StringIO(csv_content)
    reader = csv.reader(f)
    rows = list(reader)
    
    print(f"  - Total Rows Returned (including header): {len(rows)}")
    if len(rows) > 0:
        print(f"  - CSV Header: {rows[0]}")
        assert rows[0] == [
            "Event ID", "Frame", "Timestamp (s)", "Worker ID", 
            "Event Type", "Severity", "Safety Zone", "Description"
        ]
        
    # Print first few data rows
    print("\n[*] Sample Records (First 5):")
    for idx, row in enumerate(rows[1:6]):
        print(f"    {idx+1}. {row}")
        
    # 2. Test Severity Filter (e.g. CRITICAL only)
    print("\n[*] Fetching filtered audit report: CRITICAL events only...")
    response_filtered = client.get("/api/v1/reports/export?severity=CRITICAL")
    print(f"  - Status Code: {response_filtered.status_code}")
    
    f_filtered = io.StringIO(response_filtered.text)
    reader_filtered = csv.reader(f_filtered)
    rows_filtered = list(reader_filtered)
    print(f"  - CRITICAL Rows Returned: {len(rows_filtered) - 1}")
    
    # Assert all rows (except header) are CRITICAL
    if len(rows_filtered) > 1:
        for idx, row in enumerate(rows_filtered[1:]):
            assert row[5] == "CRITICAL", f"Expected CRITICAL, got {row[5]}"
        print("  - Verified: All filtered rows possess severity 'CRITICAL'.")
        
    print("=" * 60)
    print("SiteGuard AI - Step 9 safety report integration: SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    main()
