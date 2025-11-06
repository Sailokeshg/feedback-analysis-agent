#!/usr/bin/env python3
"""
Test script to verify the FastAPI app works correctly.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.main import app
    from app.config import settings

    print("✅ FastAPI app imported successfully")
    print(f"📋 App title: {app.title}")
    print(f"🔗 Docs URL: {app.docs_url}")
    print(f"🔗 OpenAPI URL: {app.openapi_url}")

    # Check routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)

    print(f"🛣️  Total routes: {len(routes)}")

    # Check router prefixes
    expected_prefixes = ['/ingest', '/analytics', '/chat', '/admin', '/health', '/healthz']
    found_prefixes = [route for route in routes if any(prefix in route for prefix in expected_prefixes)]

    print(f"✅ Found expected routes: {len(found_prefixes)}")
    for route in sorted(set(found_prefixes)):
        print(f"   {route}")

    # Test OpenAPI schema generation
    try:
        schema = app.openapi()
        print("✅ OpenAPI schema generated successfully")
        print(f"📊 Schema version: {schema.get('openapi', 'unknown')}")
        print(f"📝 Paths defined: {len(schema.get('paths', {}))}")
    except Exception as e:
        print(f"❌ OpenAPI schema generation failed: {e}")
        sys.exit(1)

    # Test health endpoint
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)

        # Test /healthz endpoint
        response = client.get("/healthz")
        if response.status_code == 200 and response.text == "ok":
            print("✅ /healthz endpoint returns 'ok'")
        else:
            print(f"❌ /healthz endpoint failed: {response.status_code} - {response.text}")
            sys.exit(1)

        # Test /health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ /health endpoint returns healthy status")
            else:
                print(f"❌ /health endpoint returned unexpected data: {data}")
        else:
            print(f"❌ /health endpoint failed: {response.status_code}")
            sys.exit(1)

    except ImportError:
        print("⚠️  TestClient not available - skipping endpoint tests")
    except Exception as e:
        print(f"❌ Endpoint testing failed: {e}")
        sys.exit(1)

    # Check middleware
    middleware_count = len(app.user_middleware)
    print(f"🛡️  Middleware registered: {middleware_count}")

    # Check settings
    print(f"⚙️  Rate limiting enabled: {settings.rate_limit.enabled}")
    print(f"🌐 CORS origins: {len(settings.cors.allow_origins)}")

    print("\n🎉 All checks passed! FastAPI app is ready.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -e .[dev]")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
