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
    azure_client_id: str | None = Field(
        default_factory=lambda: None,
        description="Azure client ID for authentication (optional)",
    )
    azure_client_secret: str = Field(..., description="Azure client secret for authentication")
    subscription_id: str | None = Field(
        default_factory=lambda: None,
        description="Azure subscription ID for resource discovery (optional)",
    )
    graph_db_url: str = Field(
        default="bolt://localhost:30000", description="Neo4j graph database connection URL"
    )
    service_bus_url: str = Field(
        default="nats://localhost:30002", description="NATS service bus connection URL"
    )
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level for the service")

    model_config = {
        "env_prefix": "TD_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("azure_client_id", "subscription_id", mode="before")
    @classmethod
    def optional_nullify_zero_uuid(cls, v: object) -> object:
        """Force well-known bogus/placeholder values and zero-UUID to None for optional fields."""
        print(f"DEBUG: Validator input for optional_nullify_zero_uuid: {v!r}")
        if not v:
            print("DEBUG: Value is None/Falsey, returning None")
            return None
        sval = str(v).strip()
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
        )
        if (
            sval == "00000000-0000-0000-0000-000000000000"
            or sval.lower().startswith("# optional")
            or not uuid_pattern.match(sval)
        ):
            print(f"DEBUG: Value {sval!r} is not a valid UUID or is a placeholder, returning None")
            return None
        print("DEBUG: Returning unmodified value")
        return v

    @field_validator("azure_tenant_id", "azure_client_id", "subscription_id")
    @classmethod
    def validate_uuid_format(cls, v: str | None, info: ValidationInfo) -> str | None:
        """Validate that the field follows UUID format, unless it's None (for optional fields)."""
        if v is None:
            return v
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


@lru_cache
def get_td_settings() -> TenantDiscoverySettings:
    """Get singleton instance of TenantDiscoverySettings.

    Uses LRU cache to ensure only one instance is created and reused.

    Returns:
        TenantDiscoverySettings: Configured settings instance
    """
    return TenantDiscoverySettings()  # type: ignore[call-arg]
