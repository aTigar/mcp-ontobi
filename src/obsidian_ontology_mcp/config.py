"""Configuration management using Pydantic Settings."""

import secrets
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    """Security-related configuration."""

    # Authentication
    enable_authentication: bool = Field(default=True)
    admin_username: str = Field(default="admin")
    admin_password_hash: str = Field(
        default="",
        description="bcrypt hash of admin password",
    )

    # JWT
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_burst: int = Field(default=10)

    # Input Validation Limits
    max_query_length: int = Field(default=1000)
    max_context_depth: int = Field(default=3)
    max_results_per_query: int = Field(default=100)
    max_concept_content_length: int = Field(default=50000)


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Vault Configuration
    vault_path: Path = Field(
        ...,
        description="Absolute path to Obsidian vault",
    )
    vault_watch_enabled: bool = Field(
        default=True,
        description="Enable file system watcher for real-time updates",
    )

    # MCP Server
    mcp_server_name: str = Field(default="Obsidian Ontology Server")
    mcp_server_version: str = Field(default="0.2.0")

    # HTTP Server
    http_host: str = Field(default="127.0.0.1")
    http_port: int = Field(default=8000)
    http_enable_cors: bool = Field(default=False)
    http_allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5678"])

    # Logging
    log_level: str = Field(default="INFO")
    log_file: Path = Field(default=Path("logs/ontology_mcp.log"))
    audit_log_file: Path = Field(default=Path("logs/audit.log"))

    # Performance
    graph_cache_enabled: bool = Field(default=True)
    graph_cache_ttl: int = Field(default=3600)

    # Security Settings
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    @field_validator("vault_path")
    @classmethod
    def validate_vault_path(cls, v: Path) -> Path:
        """Ensure vault path exists and is a directory."""
        if not v.exists():
            raise ValueError(f"Vault path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Vault path is not a directory: {v}")
        return v.resolve()

    @field_validator("log_file", "audit_log_file")
    @classmethod
    def ensure_log_directory(cls, v: Path) -> Path:
        """Create log directory if it doesn't exist."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v


# Global settings instance
settings = Settings()
