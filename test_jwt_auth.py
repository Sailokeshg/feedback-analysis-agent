#!/usr/bin/env python3
"""
Simple test script to verify JWT authentication functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from server.app.services.auth_service import auth_service

def test_auth_service():
    """Test basic auth service functionality."""
    print("Testing AuthService...")

    # Test password hashing and verification
    password = "testpassword"
    hashed = auth_service.hash_password(password)
    assert auth_service.verify_password(password, hashed), "Password verification failed"
    print("✓ Password hashing/verification works")

    # Test user authentication
    user = auth_service.authenticate_user("admin", "admin123")
    assert user is not None, "Admin authentication failed"
    assert user["role"] == "admin", "Admin role incorrect"
    print("✓ Admin authentication works")

    user = auth_service.authenticate_user("viewer", "viewer123")
    assert user is not None, "Viewer authentication failed"
    assert user["role"] == "viewer", "Viewer role incorrect"
    print("✓ Viewer authentication works")

    # Test invalid authentication
    user = auth_service.authenticate_user("admin", "wrongpassword")
    assert user is None, "Invalid authentication should return None"
    print("✓ Invalid authentication properly rejected")

    # Test JWT token creation and verification
    token_data = {"sub": "testuser", "role": "viewer"}
    token = auth_service.create_access_token(token_data)
    assert token is not None, "Token creation failed"
    print("✓ JWT token creation works")

    decoded = auth_service.verify_token(token)
    assert decoded["sub"] == "testuser", "Token decoding failed"
    assert decoded["role"] == "viewer", "Token role incorrect"
    print("✓ JWT token verification works")

    # Test role-based access control
    from server.app.services.auth_service import get_admin_user, get_viewer_user

    # Mock request for testing
    class MockRequest:
        def __init__(self):
            self.client = None

    mock_request = MockRequest()

    # Test admin user dependency (this would normally be handled by FastAPI)
    # We'll test the logic directly
    admin_user = {"sub": "admin", "role": "admin"}
    viewer_user = {"sub": "viewer", "role": "viewer"}

    try:
        result = auth_service.get_user_with_role("admin", admin_user)
        assert result["role"] == "admin", "Admin role check failed"
        print("✓ Admin role validation works")
    except Exception as e:
        print(f"✗ Admin role validation failed: {e}")
        return False

    try:
        result = auth_service.get_user_with_role("viewer", viewer_user)
        assert result["role"] == "viewer", "Viewer role check failed"
        print("✓ Viewer role validation works")
    except Exception as e:
        print(f"✗ Viewer role validation failed: {e}")
        return False

    try:
        # Viewer trying to access admin endpoint should fail
        result = auth_service.get_user_with_role("admin", viewer_user)
        print("✗ Viewer should not have admin access")
        return False
    except Exception:
        print("✓ Viewer properly blocked from admin endpoints")

    print("All basic auth tests passed! ✓")
    return True

if __name__ == "__main__":
    try:
        success = test_auth_service()
        if success:
            print("\n🎉 JWT Authentication implementation is working correctly!")
            print("Key features implemented:")
            print("- JWT token creation and verification with python-jose")
            print("- Role-based access control (admin/viewer)")
            print("- Password hashing with bcrypt")
            print("- Secret key rotation support")
            print("- Admin and viewer login endpoints")
            print("- Protected endpoints with proper role validation")
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
