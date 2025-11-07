"""
Unit tests for admin endpoints - topic relabeling and audit logging.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.main import app
from app.models import Topic, TopicAuditLog
from app.repositories import TopicRepository
from app.services.auth_service import auth_service


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session fixture."""
    return MagicMock(spec=Session)


@pytest.fixture
def topic_repo(mock_db_session):
    """Topic repository fixture."""
    return TopicRepository(mock_db_session)


@pytest.fixture
def valid_token():
    """Valid JWT token for testing."""
    token_data = {
        "sub": "admin",
        "is_admin": True,
        "role": "admin"
    }
    return auth_service.create_access_token(token_data)


class TestAdminAuthentication:
    """Test admin authentication endpoints."""

    def test_admin_login_success(self, client):
        """Test successful admin login."""
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "admin123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_admin_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "wrong"}
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.post(
            "/admin/relabel-topic",
            json={
                "topic_id": 1,
                "new_label": "New Label",
                "new_keywords": ["keyword1", "keyword2"]
            }
        )

        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.post(
            "/admin/relabel-topic",
            headers={"Authorization": "Bearer invalid.token.here"},
            json={
                "topic_id": 1,
                "new_label": "New Label",
                "new_keywords": ["keyword1", "keyword2"]
            }
        )

        assert response.status_code == 401


class TestTopicRepository:
    """Test topic repository functionality."""

    def test_update_topic_label_success(self, topic_repo, mock_db_session):
        """Test successful topic label update with audit logging."""
        # Mock existing topic
        mock_topic = Topic(
            id=1,
            label="Old Label",
            keywords=["old", "keywords"],
            updated_at=datetime.utcnow()
        )

        # Mock repository methods
        topic_repo.get_topic_by_id = MagicMock(return_value=mock_topic)
        topic_repo.session.add = MagicMock()
        topic_repo.session.commit = MagicMock()
        topic_repo.session.refresh = MagicMock()

        # Update topic
        result = topic_repo.update_topic_label(
            topic_id=1,
            new_label="New Label",
            new_keywords=["new", "keywords"],
            changed_by="admin",
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )

        # Verify topic was updated
        assert result.label == "New Label"
        assert result.keywords == ["new", "keywords"]

        # Verify audit log was created
        topic_repo.session.add.assert_called_once()
        audit_log_call = topic_repo.session.add.call_args[0][0]
        assert isinstance(audit_log_call, TopicAuditLog)
        assert audit_log_call.topic_id == 1
        assert audit_log_call.action == "update"
        assert audit_log_call.old_label == "Old Label"
        assert audit_log_call.new_label == "New Label"
        assert audit_log_call.changed_by == "admin"

        # Verify commit was called
        topic_repo.session.commit.assert_called_once()
        topic_repo.session.refresh.assert_called_once_with(mock_topic)

    def test_update_topic_label_not_found(self, topic_repo, mock_db_session):
        """Test topic update when topic doesn't exist."""
        topic_repo.get_topic_by_id = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="Topic with ID 999 not found"):
            topic_repo.update_topic_label(
                topic_id=999,
                new_label="New Label",
                new_keywords=["new", "keywords"],
                changed_by="admin"
            )

    def test_get_topic_audit_history(self, topic_repo, mock_db_session):
        """Test getting audit history for a topic."""
        # Mock audit logs
        mock_logs = [
            TopicAuditLog(
                id=1,
                topic_id=1,
                action="update",
                old_label="Old",
                new_label="New",
                changed_by="admin",
                changed_at=datetime.utcnow()
            )
        ]

        # Mock query
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_logs
        topic_repo.session.query.return_value = mock_query

        result = topic_repo.get_topic_audit_history(1)

        assert len(result) == 1
        assert result[0]["action"] == "update"
        assert result[0]["old_label"] == "Old"
        assert result[0]["new_label"] == "New"

    def test_get_recent_audit_logs(self, topic_repo, mock_db_session):
        """Test getting recent audit logs across all topics."""
        # Mock audit logs with joins
        mock_logs = [
            (TopicAuditLog(
                id=1,
                topic_id=1,
                action="update",
                changed_by="admin",
                changed_at=datetime.utcnow()
            ), "Topic Label")
        ]

        # Mock query with joins
        mock_query = MagicMock()
        mock_query.join.return_value.order_by.return_value.limit.return_value.all.return_value = mock_logs
        topic_repo.session.query.return_value = mock_query

        result = topic_repo.get_recent_audit_logs(10)

        assert len(result) == 1
        assert result[0]["topic_label"] == "Topic Label"


class TestAdminEndpoints:
    """Test admin API endpoints."""

    def test_relabel_topic_success(self, client, valid_token, mock_db_session):
        """Test successful topic relabeling."""
        # Mock topic
        mock_topic = Topic(
            id=1,
            label="Old Label",
            keywords=["old"],
            updated_at=datetime.utcnow()
        )

        # Mock repository
        with patch('app.repositories.TopicRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_topic_by_id.return_value = mock_topic
            mock_repo.update_topic_label.return_value = Topic(
                id=1,
                label="New Label",
                keywords=["new"],
                updated_at=datetime.utcnow()
            )
            mock_repo_class.return_value = mock_repo

            response = client.post(
                "/admin/relabel-topic",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "topic_id": 1,
                    "new_label": "New Label",
                    "new_keywords": ["new", "keywords"]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["topic_id"] == 1
            assert data["old_label"] == "Old Label"
            assert data["new_label"] == "New Label"
            assert data["old_keywords"] == ["old"]
            assert data["new_keywords"] == ["new"]

    def test_relabel_topic_not_found(self, client, valid_token):
        """Test relabeling non-existent topic."""
        with patch('app.repositories.TopicRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_topic_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = client.post(
                "/admin/relabel-topic",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "topic_id": 999,
                    "new_label": "New Label",
                    "new_keywords": ["new"]
                }
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_topic_audit_history(self, client, valid_token):
        """Test getting topic audit history."""
        with patch('app.repositories.TopicRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_topic_audit_history.return_value = [
                {
                    "id": 1,
                    "action": "update",
                    "old_label": "Old",
                    "new_label": "New",
                    "changed_by": "admin",
                    "changed_at": "2024-01-01T00:00:00"
                }
            ]
            mock_repo_class.return_value = mock_repo

            response = client.get(
                "/admin/topic-audit/1",
                headers={"Authorization": f"Bearer {valid_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["topic_id"] == 1
            assert len(data["audit_logs"]) == 1
            assert data["audit_logs"][0]["action"] == "update"

    def test_get_recent_audit_logs(self, client, valid_token):
        """Test getting recent audit logs."""
        with patch('app.repositories.TopicRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_recent_audit_logs.return_value = [
                {
                    "id": 1,
                    "topic_id": 1,
                    "topic_label": "Test Topic",
                    "action": "update",
                    "changed_by": "admin",
                    "changed_at": "2024-01-01T00:00:00"
                }
            ]
            mock_repo_class.return_value = mock_repo

            response = client.get(
                "/admin/topic-audit",
                headers={"Authorization": f"Bearer {valid_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["topic_label"] == "Test Topic"


class TestAuthService:
    """Test authentication service functionality."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        token_data = {"sub": "admin", "is_admin": True}
        token = auth_service.create_access_token(token_data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test verifying a valid JWT token."""
        token_data = {"sub": "admin", "is_admin": True}
        token = auth_service.create_access_token(token_data)

        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == "admin"
        assert decoded["is_admin"] is True

    def test_verify_invalid_token(self):
        """Test verifying an invalid JWT token."""
        with pytest.raises(Exception):  # Should raise JWT error
            auth_service.verify_token("invalid.token.here")

    def test_verify_expired_token(self):
        """Test verifying an expired JWT token."""
        # Create token that expires immediately
        import time
        token_data = {"sub": "admin", "exp": int(time.time()) - 1}
        token = auth_service.create_access_token(token_data)

        with pytest.raises(Exception):  # Should raise expired error
            auth_service.verify_token(token)


class TestRoleBasedAuthentication:
    """Test role-based authentication with JWT."""

    def test_admin_login_success(self, client):
        """Test successful admin login."""
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "admin123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_viewer_login_success(self, client):
        """Test successful viewer login."""
        response = client.post(
            "/admin/viewer/login",
            json={"username": "viewer", "password": "viewer123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_admin_login_invalid_credentials(self, client):
        """Test admin login with invalid credentials."""
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "wrong"}
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_viewer_login_invalid_credentials(self, client):
        """Test viewer login with invalid credentials."""
        response = client.post(
            "/admin/viewer/login",
            json={"username": "viewer", "password": "wrong"}
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_admin_login_wrong_role(self, client):
        """Test admin login with viewer credentials."""
        response = client.post(
            "/admin/login",
            json={"username": "viewer", "password": "viewer123"}
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


class TestRoleBasedAccessControl:
    """Test role-based access control for protected endpoints."""

    @pytest.fixture
    def admin_token(self, client):
        """Get admin JWT token."""
        response = client.post(
            "/admin/login",
            json={"username": "admin", "password": "admin123"}
        )
        return response.json()["access_token"]

    @pytest.fixture
    def viewer_token(self, client):
        """Get viewer JWT token."""
        response = client.post(
            "/admin/viewer/login",
            json={"username": "viewer", "password": "viewer123"}
        )
        return response.json()["access_token"]

    def test_admin_endpoints_require_authentication(self, client):
        """Test that admin endpoints block unauthorized access."""
        admin_endpoints = [
            "/admin/stats",
            "/admin/relabel-topic",
            "/admin/topic-audit/1",
            "/admin/topic-audit",
            "/admin/maintenance/refresh-materialized-view",
            "/admin/health/database",
            "/admin/config",
            "/admin/cleanup/old-data",
            "/admin/logs/recent",
            "/admin/cache/clear"
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"

    def test_viewer_endpoints_require_authentication(self, client):
        """Test that viewer endpoints block unauthorized access."""
        viewer_endpoints = [
            "/admin/viewer/stats",
            "/admin/viewer/dashboard",
            "/admin/viewer/profile"
        ]

        for endpoint in viewer_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"

    def test_viewer_can_access_viewer_endpoints(self, client, viewer_token):
        """Test that viewers can access viewer endpoints."""
        headers = {"Authorization": f"Bearer {viewer_token}"}

        # Test viewer stats
        response = client.get("/admin/viewer/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_feedback" in data
        assert data["user_role"] == "viewer"

        # Test viewer dashboard
        response = client.get("/admin/viewer/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert "sentiment_trends" in data

        # Test viewer profile
        response = client.get("/admin/viewer/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "viewer"
        assert "read:stats" in data["permissions"]

    def test_admin_can_access_all_endpoints(self, client, admin_token):
        """Test that admins can access all endpoints."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Test admin can access viewer endpoints
        response = client.get("/admin/viewer/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_role"] == "admin"

        # Test admin profile shows admin permissions
        response = client.get("/admin/viewer/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert "admin:system" in data["permissions"]

        # Test admin can access admin-only endpoints
        response = client.get("/admin/stats", headers=headers)
        assert response.status_code == 200

    def test_viewer_cannot_access_admin_endpoints(self, client, viewer_token):
        """Test that viewers cannot access admin-only endpoints."""
        headers = {"Authorization": f"Bearer {viewer_token}"}

        admin_endpoints = [
            "/admin/stats",
            "/admin/relabel-topic",
            "/admin/topic-audit/1",
            "/admin/topic-audit",
            "/admin/maintenance/refresh-materialized-view",
            "/admin/health/database",
            "/admin/config",
            "/admin/cleanup/old-data",
            "/admin/logs/recent",
            "/admin/cache/clear"
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 403, f"Viewer should not access admin endpoint {endpoint}"
            assert "Admin privileges required" in response.json()["detail"]

    def test_invalid_token_rejected(self, client):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid.token.here"}

        response = client.get("/admin/viewer/stats", headers=headers)
        assert response.status_code == 401

    def test_expired_token_rejected(self, client):
        """Test that expired tokens are rejected."""
        # Create an expired token
        import time
        expired_token_data = {
            "sub": "viewer",
            "role": "viewer",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }
        expired_token = auth_service.create_access_token(expired_token_data)

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/admin/viewer/stats", headers=headers)
        assert response.status_code == 401
        assert "Token has expired" in response.json()["detail"]

    def test_malformed_token_rejected(self, client):
        """Test that malformed tokens are rejected."""
        headers = {"Authorization": "Bearer not-a-jwt-token"}

        response = client.get("/admin/viewer/stats", headers=headers)
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]
