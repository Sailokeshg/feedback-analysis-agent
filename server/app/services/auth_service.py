"""
JWT authentication service with role-based access control for admin and viewer endpoints.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Literal
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from ..config import settings

security = HTTPBearer()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UserRole = Literal["admin", "viewer"]


class AuthService:
    """JWT authentication service with role-based access control."""

    def __init__(self):
        self.secret_key = settings.security.secret_key
        self.secret_key_rotation = settings.security.secret_key_rotation or self.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes

        # User credentials (for development/demo only)
        self.users = {
            settings.security.admin_username: {
                "username": settings.security.admin_username,
                "password": self.hash_password(settings.security.admin_password),
                "role": "admin",
                "disabled": False
            },
            settings.security.viewer_username: {
                "username": settings.security.viewer_username,
                "password": self.hash_password(settings.security.viewer_password),
                "role": "viewer",
                "disabled": False
            }
        }

    def hash_password(self, password: str) -> str:
        """Hash a password for storing."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user by username and password."""
        user = self.users.get(username)
        if not user:
            return None
        if not self.verify_password(password, user["password"]):
            return None
        if user["disabled"]:
            return None
        return user

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token, supporting secret rotation."""
        # Try primary secret first
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.InvalidTokenError:
            # Try rotation secret if primary fails
            if self.secret_key_rotation and self.secret_key_rotation != self.secret_key:
                try:
                    payload = jwt.decode(token, self.secret_key_rotation, algorithms=[self.algorithm])
                    return payload
                except jwt.InvalidTokenError:
                    pass

            # If both fail, raise appropriate error
            try:
                # Check if it's an expired token
                jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
                raise HTTPException(status_code=401, detail="Token has expired")
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid token")

    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Dependency to get current authenticated user."""
        return self.verify_token(credentials.credentials)

    def get_user_with_role(self, required_role: UserRole, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Dependency to ensure user has required role privileges."""
        user_role = current_user.get("role")
        if not user_role:
            raise HTTPException(status_code=403, detail="User role not specified in token")

        if user_role not in ["admin", "viewer"]:
            raise HTTPException(status_code=403, detail="Invalid user role")

        if required_role == "admin" and user_role != "admin":
            raise HTTPException(status_code=403, detail="Admin privileges required")

        # Viewer role has access to viewer endpoints, admin has access to both
        if required_role == "viewer" and user_role not in ["admin", "viewer"]:
            raise HTTPException(status_code=403, detail="Viewer privileges required")

        return current_user

    def get_admin_user(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Dependency to ensure user has admin privileges."""
        return self.get_user_with_role("admin", current_user)

    def get_viewer_user(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Dependency to ensure user has at least viewer privileges."""
        return self.get_user_with_role("viewer", current_user)


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
    return auth_service.get_user_with_role("admin", current_user)


def get_viewer_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency to ensure user has at least viewer privileges."""
    return auth_service.get_user_with_role("viewer", current_user)
