#!/usr/bin/env python3
"""
Manual test script for ingestion endpoint.
Run this after starting the server to test the ingestion functionality.
"""

import requests
import time
import os

# Server URL - adjust if running on different port
BASE_URL = "http://localhost:8001"

def test_csv_ingestion():
    """Test CSV file ingestion."""
    print("Testing CSV ingestion...")

    csv_file_path = os.path.join(os.path.dirname(__file__), "test_data", "sample_feedback.csv")

    if not os.path.exists(csv_file_path):
        print(f"❌ CSV test file not found: {csv_file_path}")
        return

    with open(csv_file_path, 'rb') as f:
        files = {'file': ('sample_feedback.csv', f, 'text/csv')}
        data = {'source': 'test_csv', 'process_async': 'true'}

        try:
            response = requests.post(f"{BASE_URL}/ingest/", files=files, data=data)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("✅ CSV ingestion successful!"                print(f"   Batch ID: {result['batch_id']}")
                print(f"   Processed: {result['processed_count']}")
                print(f"   Created: {result['created_count']}")
                print(f"   Duplicates: {result['duplicate_count']}")
                print(f"   Errors: {result['error_count']}")
                if result.get('job_id'):
                    print(f"   Job ID: {result['job_id']}")
            else:
                print(f"❌ CSV ingestion failed: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")

def test_jsonl_ingestion():
    """Test JSONL file ingestion."""
    print("\nTesting JSONL ingestion...")

    jsonl_file_path = os.path.join(os.path.dirname(__file__), "test_data", "sample_feedback.jsonl")

    if not os.path.exists(jsonl_file_path):
        print(f"❌ JSONL test file not found: {jsonl_file_path}")
        return

    with open(jsonl_file_path, 'rb') as f:
        files = {'file': ('sample_feedback.jsonl', f, 'application/json')}
        data = {'source': 'test_jsonl', 'process_async': 'true'}

        try:
            response = requests.post(f"{BASE_URL}/ingest/", files=files, data=data)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("✅ JSONL ingestion successful!"                print(f"   Batch ID: {result['batch_id']}")
                print(f"   Processed: {result['processed_count']}")
                print(f"   Created: {result['created_count']}")
                print(f"   Duplicates: {result['duplicate_count']}")
                print(f"   Errors: {result['error_count']}")
                if result.get('job_id'):
                    print(f"   Job ID: {result['job_id']}")
            else:
                print(f"❌ JSONL ingestion failed: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")

def test_duplicate_detection():
    """Test duplicate detection by uploading the same file twice."""
    print("\nTesting duplicate detection...")

    csv_file_path = os.path.join(os.path.dirname(__file__), "test_data", "sample_feedback.csv")

    if not os.path.exists(csv_file_path):
        print(f"❌ CSV test file not found: {csv_file_path}")
        return

    # First upload
    print("First upload:")
    with open(csv_file_path, 'rb') as f:
        files = {'file': ('sample_feedback.csv', f, 'text/csv')}
        data = {'source': 'test_duplicates', 'process_async': 'false'}

        try:
            response = requests.post(f"{BASE_URL}/ingest/", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                print(f"   Created: {result['created_count']}, Duplicates: {result['duplicate_count']}")
            else:
                print(f"❌ First upload failed: {response.status_code}")
                return
        except requests.exceptions.RequestException as e:
            print(f"❌ First upload request failed: {e}")
            return

    # Second upload (should detect duplicates)
    print("Second upload (should detect duplicates):")
    with open(csv_file_path, 'rb') as f:
        files = {'file': ('sample_feedback.csv', f, 'text/csv')}
        data = {'source': 'test_duplicates', 'process_async': 'false'}

        try:
            response = requests.post(f"{BASE_URL}/ingest/", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                print(f"   Created: {result['created_count']}, Duplicates: {result['duplicate_count']}")

                if result['duplicate_count'] > 0:
                    print("✅ Duplicate detection working!")
                else:
                    print("⚠️  No duplicates detected (might be expected if data was modified)")
            else:
                print(f"❌ Second upload failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Second upload request failed: {e}")

def test_health_check():
    """Test health check endpoints."""
    print("\nTesting health checks...")

    # Test /healthz
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        if response.status_code == 200 and response.text == "ok":
            print("✅ /healthz endpoint working")
        else:
            print(f"❌ /healthz endpoint failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ /healthz request failed: {e}")

    # Test /health
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ /health endpoint working")
            else:
                print(f"❌ /health endpoint returned unexpected data: {data}")
        else:
            print(f"❌ /health endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ /health request failed: {e}")

def main():
    """Run all ingestion tests."""
    print("🚀 Starting ingestion endpoint tests...")
    print(f"Server URL: {BASE_URL}")
    print("=" * 50)

    # Test health endpoints first
    test_health_check()

    # Test CSV ingestion
    test_csv_ingestion()

    # Test JSONL ingestion
    test_jsonl_ingestion()

    # Test duplicate detection
    test_duplicate_detection()

    print("\n" + "=" * 50)
    print("✨ Ingestion tests completed!")
    print("\nNext steps:")
    print("1. Check the database for inserted feedback")
    print("2. Monitor RQ worker for background processing jobs")
    print("3. Check analytics endpoints for processed data")

if __name__ == "__main__":
    main()
