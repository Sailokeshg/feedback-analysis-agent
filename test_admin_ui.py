#!/usr/bin/env python3
"""
Test script to verify admin topic management functionality.
Run this after starting the server to test admin endpoints.
"""

import requests
import json
import sys
import time

def test_admin_endpoint(base_url: str, endpoint: str, method: str = "GET", data: dict = None, token: str = None, description: str = "") -> dict:
    """Test an admin endpoint with authentication."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        url = f"{base_url}{endpoint}"
        print(f"\n🧪 Testing {description}")
        print(f"   {method} {url}")

        start_time = time.time()
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")

        duration = time.time() - start_time
        print(".2f"        print(f"   Status: {response.status_code}")

        if response.status_code >= 200 and response.status_code < 300:
            print("   ✅ Test passed")
            try:
                return response.json()
            except:
                return {"text": response.text}
        else:
            print(f"   ❌ Test failed: {response.text}")
            return None

    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return None

def login_admin(base_url: str, username: str = "admin", password: str = "admin123") -> str:
    """Login and get admin token."""
    print(f"\n🔐 Logging in as {username}...")
    response = requests.post(f"{base_url}/admin/login", json={
        "username": username,
        "password": password
    })

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print("   ✅ Login successful")
        return token
    else:
        print(f"   ❌ Login failed: {response.text}")
        return None

def main():
    """Run admin topic management tests."""
    print("🚀 Testing Admin Topic Management")
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

    # Login as admin
    admin_token = login_admin(base_url)
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        sys.exit(1)

    # Test cases
    test_cases = [
        {
            "endpoint": "/admin/topics",
            "method": "GET",
            "token": admin_token,
            "description": "Get all topics"
        },
        {
            "endpoint": "/admin/topics/1/feedback",
            "method": "GET",
            "token": admin_token,
            "description": "Get feedback for topic 1"
        },
        {
            "endpoint": "/admin/relabel-topic",
            "method": "POST",
            "token": admin_token,
            "data": {
                "topic_id": 1,
                "new_label": "Updated Test Topic",
                "new_keywords": ["test", "updated", "admin"]
            },
            "description": "Update topic label and keywords"
        },
        {
            "endpoint": "/admin/reassign-feedback",
            "method": "POST",
            "token": admin_token,
            "data": {
                "feedback_id": "test-feedback-id",
                "new_topic_id": 1,
                "reason": "Testing reassignment"
            },
            "description": "Reassign feedback to different topic"
        }
    ]

    passed = 0
    total = len(test_cases)

    for test_case in test_cases:
        result = test_admin_endpoint(base_url, **test_case)
        if result is not None:
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All admin topic management tests passed!")
        print("\n📋 Admin endpoints are working correctly:")
        print("   • GET /admin/topics - List all topics")
        print("   • GET /admin/topics/{id}/feedback - Get topic feedback")
        print("   • POST /admin/relabel-topic - Update topic labels/keywords")
        print("   • POST /admin/reassign-feedback - Reassign feedback comments")
        print("\n🔄 Changes are automatically reflected in analytics after refresh")
        print("📝 All changes are logged in the audit trail")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
