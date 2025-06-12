"""Tenant Discovery Configuration Settings."""

import re
from enum import Enum
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field
from pydantic import ValidationInfo
from pydantic import field_validator
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    """Available log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class TenantDiscoverySettings(BaseSettings):
    """Configuration settings for Tenant Discovery service."""

    azure_tenant_id: str = Field(..., description="Azure tenant ID for authentication")
    azure_client_id: str = Field(..., description="Azure client ID for authentication")
    azure_client_secret: str = Field(..., description="Azure client secret for authentication")
    subscription_id: str = Field(..., description="Azure subscription ID for resource discovery")
    graph_db_url: str = Field(
        default="bolt://localhost:30000", description="Neo4j graph database connection URL"
    )
    service_bus_url: str = Field(
        default="nats://localhost:30002", description="NATS service bus connection URL"
    )
    api_base_url: str = Field(
        default="http://localhost:8001", description="SimBuilder API base URL"
    )
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level for the service")

    model_config = {
        "env_prefix": "TD_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("azure_tenant_id", "azure_client_id", "subscription_id")
    @classmethod
    def validate_uuid_format(cls, v: str, info: ValidationInfo) -> str:
        """Validate that the field follows UUID format."""
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError(f"{info.field_name} must be a valid UUID format")
        return v

    @field_validator("graph_db_url")
    @classmethod
    def validate_graph_db_url(cls, v: str) -> str:
        """Validate that graph_db_url has correct scheme."""
        parsed = urlparse(v)
        if parsed.scheme not in ["bolt", "bolt+s", "bolt+ssc", "neo4j", "neo4j+s", "neo4j+ssc"]:
            raise ValueError(
                "graph_db_url must use a valid Neo4j scheme "
                "(bolt, bolt+s, bolt+ssc, neo4j, neo4j+s, neo4j+ssc)"
            )
        return v

    @field_validator("service_bus_url")
    @classmethod
    def validate_service_bus_url(cls, v: str) -> str:
        """Validate that service_bus_url has correct scheme."""
        parsed = urlparse(v)
        if parsed.scheme not in ["nats", "nats+tls"]:
            raise ValueError("service_bus_url must use nats:// or nats+tls:// scheme")
        return v

    @field_validator("api_base_url")
    @classmethod
    def validate_api_base_url(cls, v: str) -> str:
        """Validate that api_base_url has correct scheme."""
        parsed = urlparse(v)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("api_base_url must use http:// or https:// scheme")
        return v


@lru_cache
def get_td_settings() -> TenantDiscoverySettings:
    """Get singleton instance of TenantDiscoverySettings.

    Uses LRU cache to ensure only one instance is created and reused.

    Returns:
        TenantDiscoverySettings: Configured settings instance
    """
    return TenantDiscoverySettings()  # type: ignore[call-arg]
