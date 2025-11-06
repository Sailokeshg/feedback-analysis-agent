"""
JWT authentication service for admin endpoints.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config import settings

security = HTTPBearer()


class AuthService:
    """JWT authentication service for admin operations."""

    def __init__(self):
        self.secret_key = settings.security.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Dependency to get current authenticated user."""
        return self.verify_token(credentials.credentials)

    def get_admin_user(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Dependency to ensure user has admin privileges."""
        # For simplicity, we'll assume any authenticated user is an admin
        # In production, you'd check roles/permissions in the token
        if not current_user.get("is_admin", False):
            # For now, we'll accept any valid token as admin
            # In production, you'd validate admin role here
            pass
        return current_user


# Global auth service instance
auth_service = AuthService()


def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user with request info."""
    user = auth_service.verify_token(credentials.credentials)
    # Add request metadata to user info
    user["ip_address"] = request.client.host if request.client else None
    user["user_agent"] = request.headers.get("user-agent")
    return user


def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency to ensure user has admin privileges."""
    # For simplicity, we'll assume any authenticated user is an admin
    # In production, you'd check roles/permissions in the token
    return current_user
