"""
Configuration management for SimBuilder using Pydantic settings.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from .exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Azure Authentication
    azure_tenant_id: str = Field(..., description="Azure tenant identifier")
    azure_subscription_id: str | None = Field(
        None,
        description="Azure subscription identifier (optional for tests/CLI)"
    )
    azure_client_id: str | None = Field(None, description="Service principal client ID")
    azure_client_secret: str | None = Field(None, description="Service principal secret")

    # Graph Database
    neo4j_uri: str = Field("neo4j://localhost:7687", description="Neo4j connection string")
    neo4j_user: str = Field("neo4j", description="Neo4j username")
    neo4j_password: str = Field(..., description="Neo4j password")
    neo4j_database: str = Field("simbuilder", description="Neo4j database name")

    # Service Bus
    service_bus_url: str = Field("nats://localhost:4222", description="NATS JetStream connection")
    service_bus_cluster_id: str = Field("simbuilder-local", description="NATS cluster identifier")

    # LLM Integration
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI service endpoint")
    azure_openai_key: str = Field(..., description="Azure OpenAI API key")
    azure_openai_api_version: str = Field("2024-02-15-preview", description="API version")
    azure_openai_model_chat: str = Field("gpt-4o", description="Chat completion model")
    azure_openai_model_reasoning: str = Field("gpt-4o", description="Text completion model")

    # Core API Service
    core_api_url: str = Field("http://localhost:7000", description="Core API base URL")
    core_api_port: int = Field(7000, description="Core API listening port")
    jwt_secret: str = Field("insecure-dev-secret", description="JWT signing secret")

    # Application Configuration
    log_level: str = Field("INFO", description="Application log level")
    environment: str = Field("development", description="Runtime environment")
    debug_mode: bool = Field(False, description="Enable debug features")

    # Spec Library
    spec_repo_url: str = Field("https://github.com/SimBuilder/spec-library.git", description="Spec repository URL")
    spec_repo_branch: str = Field("main", description="Spec repository branch")

    @field_validator("azure_openai_endpoint")
    @classmethod
    def validate_openai_endpoint(cls, v: str) -> str:
        """Ensure OpenAI endpoint ends with /."""
        if not v.endswith("/"):
            v += "/"
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is supported."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'value_error',
                f"Log level must be one of: {', '.join(valid_levels)}",
                {'reason': f"Log level must be one of: {', '.join(valid_levels)}"}
            )
        return v_upper

    @field_validator("core_api_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is in valid range."""
        if not 1024 <= v <= 65535:
            from pydantic_core import PydanticCustomError
            raise PydanticCustomError(
                'value_error',
                "Port must be between 1024 and 65535",
                {'reason': "Port must be between 1024 and 65535"}
            )
        return v

    def validate_required_for_environment(self) -> None:
        """Validate that required settings are present for the current environment."""
        if self.environment == "production":
            required_fields = [
                "azure_tenant_id",
                "neo4j_password",
                "azure_openai_endpoint",
                "azure_openai_key"
            ]

            missing = []
            for field in required_fields:
                if getattr(self, field) in (None, ""):
                    missing.append(field.upper())

            if missing:
                raise ConfigurationError(
                    f"Missing required configuration for production environment: {', '.join(missing)}"
                )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    try:
        settings = Settings()
        settings.validate_required_for_environment()
        return settings
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    # Go up from src/scaffolding/config.py to project root
    return current.parent.parent.parent


def get_env_file_path() -> Path:
    """Get the path to the .env file."""
    return get_project_root() / ".env"


def create_env_template() -> None:
    """Create a .env.template file with all configuration options."""
    template_path = get_project_root() / ".env.template"

    template_content = """# SimBuilder Environment Configuration

# Azure Authentication
AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1
AZURE_CLIENT_ID=  # Optional: Service principal client ID
AZURE_CLIENT_SECRET=  # Optional: Service principal secret

# Graph Database
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
NEO4J_DATABASE=simbuilder

# Service Bus
SERVICE_BUS_URL=nats://localhost:4222
SERVICE_BUS_CLUSTER_ID=simbuilder-local

# LLM Integration
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MODEL_CHAT=gpt-4o
AZURE_OPENAI_MODEL_REASONING=gpt-4o

# Core API Service
CORE_API_URL=http://localhost:7000
CORE_API_PORT=7000
JWT_SECRET=insecure-dev-secret

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG_MODE=true

# Spec Library
SPEC_REPO_URL=https://github.com/SimBuilder/spec-library.git
SPEC_REPO_BRANCH=main
SPEC_REPO_TOKEN=  # Optional: Git access token for private repositories
"""

    with open(template_path, "w", encoding="utf-8") as f:
        f.write(template_content.strip())
