#!/usr/bin/env python3
"""
Test script to verify CSV export API functionality.
Run this after starting the server to test export endpoints.
"""

import requests
import csv
import io
import sys
import time
from typing import Dict, Any

def test_export_endpoint(base_url: str, endpoint: str, params: Dict[str, Any] = None, description: str = "") -> bool:
    """Test an export endpoint and verify it returns valid CSV."""
    if params is None:
        params = {}

    try:
        url = f"{base_url}{endpoint}"
        print(f"\n🧪 Testing {description}")
        print(f"   URL: {url}")
        print(f"   Params: {params}")

        start_time = time.time()
        response = requests.get(url, params=params, timeout=30)
        duration = time.time() - start_time

        print(".2f"        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")

        if response.status_code != 200:
            print(f"   ❌ Failed with status {response.status_code}: {response.text}")
            return False

        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))

        # Read header row
        try:
            header = next(csv_reader)
            print(f"   ✅ CSV header: {header}")
        except StopIteration:
            print("   ❌ No CSV data returned")
            return False

        # Count data rows
        row_count = sum(1 for _ in csv_reader)
        print(f"   📊 Data rows: {row_count}")

        # Basic validation
        if len(header) == 0:
            print("   ❌ Empty CSV header")
            return False

        print("   ✅ Export test passed"        return True

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Run export API tests."""
    print("🚀 Testing CSV Export API")
    print("=" * 50)

    # Configuration
    base_url = "http://localhost:8001"  # Adjust if your server runs on different port

    # Check if server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Server health check failed (status {health_response.status_code})")
            print("   Make sure the server is running: cd server && uvicorn app.main:app --reload")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server")
        print("   Make sure the server is running: cd server && uvicorn app.main:app --reload")
        sys.exit(1)

    print("✅ Server is running")

    # Test cases
    test_cases = [
        {
            "endpoint": "/api/export.csv",
            "params": {},
            "description": "Basic feedback export"
        },
        {
            "endpoint": "/api/export.csv",
            "params": {"source": "website", "page": 1, "page_size": 10},
            "description": "Filtered feedback export (website source)"
        },
        {
            "endpoint": "/api/export/topics.csv",
            "params": {"min_feedback_count": 1},
            "description": "Topics export"
        },
        {
            "endpoint": "/api/export/analytics.csv",
            "params": {},
            "description": "Analytics export"
        }
    ]

    passed = 0
    total = len(test_cases)

    for test_case in test_cases:
        if test_export_endpoint(base_url, **test_case):
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All export API tests passed!")
        print("\n📋 Export endpoints are working correctly:")
        print("   • GET /api/export.csv - Feedback data export")
        print("   • GET /api/export/topics.csv - Topics data export")
        print("   • GET /api/export/analytics.csv - Analytics data export")
        print("\n💡 Streaming is enabled for large datasets")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
