"""
Application configuration using Pydantic settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str = Field(default="postgresql://user:password@localhost:5432/feedback_db")
    pool_size: int = Field(default=10, gt=0)
    max_overflow: int = Field(default=20, ge=0)
    pool_pre_ping: bool = Field(default=True)

    class Config:
        env_prefix = "DATABASE_"


class APISettings(BaseSettings):
    """API configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, gt=0, le=65535)
    debug: bool = Field(default=False)
    title: str = Field(default="AI Customer Insights Agent API")
    description: str = Field(default="API for processing and analyzing customer feedback")
    version: str = Field(default="0.1.0")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    openapi_url: str = Field(default="/openapi.json")

    class Config:
        env_prefix = "API_"


class CORSSettings(BaseSettings):
    """CORS configuration."""
    allow_origins: List[str] = Field(default=["http://localhost:3000"])
    allow_credentials: bool = Field(default=True)
    allow_methods: List[str] = Field(default=["*"])
    allow_headers: List[str] = Field(default=["*"])
    max_age: int = Field(default=86400, gt=0)  # 24 hours

    class Config:
        env_prefix = "CORS_"


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""
    enabled: bool = Field(default=True)
    requests_per_minute: int = Field(default=60, gt=0)
    burst_limit: int = Field(default=10, gt=0)

    class Config:
        env_prefix = "RATE_LIMIT_"


class SecuritySettings(BaseSettings):
    """Security configuration."""
    # JWT Configuration
    secret_key: str = Field(default="your-secret-key-change-in-production")
    secret_key_rotation: str = Field(default="", description="Secondary secret key for rotation")
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)

    # User Credentials (for development/demo only)
    admin_username: str = Field(default="admin")
    admin_password: str = Field(default="admin123")
    viewer_username: str = Field(default="viewer")
    viewer_password: str = Field(default="viewer123")

    class Config:
        env_prefix = "SECURITY_"


class ExternalServicesSettings(BaseSettings):
    """External services configuration."""
    chroma_url: str = Field(default="http://localhost:8000")
    redis_url: Optional[str] = Field(default="redis://localhost:6379")

    class Config:
        env_prefix = "EXTERNAL_"


class Settings(BaseSettings):
    """Main application settings."""
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    cors: CORSSettings = CORSSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    security: SecuritySettings = SecuritySettings()
    external: ExternalServicesSettings = ExternalServicesSettings()

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
