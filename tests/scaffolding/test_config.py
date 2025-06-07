"""
Unit tests for scaffolding configuration module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.scaffolding.config import Settings, get_settings, create_env_template
from src.scaffolding.exceptions import ConfigurationError


class TestSettings:
    """Test the Settings class."""

    def test_required_fields_validation(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        errors = exc_info.value.errors()
        required_fields = {error["loc"][0] for error in errors if error["type"] == "missing"}
        
        # Check that core required fields are present
        assert "azure_tenant_id" in required_fields
        assert "neo4j_password" in required_fields
        assert "azure_openai_endpoint" in required_fields
        assert "azure_openai_key" in required_fields

    def test_default_values(self):
        """Test that default values are set correctly."""
        # Provide minimal required config
        settings = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="test-password",
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key"
        )
        
        assert settings.neo4j_uri == "neo4j://localhost:7687"
        assert settings.neo4j_user == "neo4j"
        assert settings.neo4j_database == "simbuilder"
        assert settings.service_bus_url == "nats://localhost:4222"
        assert settings.service_bus_cluster_id == "simbuilder-local"
        assert settings.core_api_url == "http://localhost:7000"
        assert settings.core_api_port == 7000
        assert settings.log_level == "INFO"
        assert settings.environment == "development"
        assert settings.debug_mode is False

    def test_openai_endpoint_validation(self):
        """Test OpenAI endpoint URL validation."""
        settings = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="test-password",
            azure_openai_endpoint="https://test.openai.azure.com",  # No trailing slash
            azure_openai_key="test-key"
        )
        
        # Should add trailing slash
        assert settings.azure_openai_endpoint == "https://test.openai.azure.com/"

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log level
        settings = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="test-password",
            azure_openai_endpoint="https://test.openai.azure.com/",
            azure_openai_key="test-key",
            log_level="DEBUG"
        )
        assert settings.log_level == "DEBUG"
        
        # Invalid log level
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                azure_tenant_id="test-tenant",
                neo4j_password="test-password",
                azure_openai_endpoint="https://test.openai.azure.com/",
                azure_openai_key="test-key",
                log_level="INVALID"
            )
        
        errors = exc_info.value.errors()
        assert any("Log level must be one of" in str(error["ctx"]["reason"]) for error in errors)

    def test_port_validation(self):
        """Test port number validation."""
        # Valid port
        settings = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="test-password",
            azure_openai_endpoint="https://test.openai.azure.com/",
            azure_openai_key="test-key",
            core_api_port=8080
        )
        assert settings.core_api_port == 8080
        
        # Invalid port (too low)
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                azure_tenant_id="test-tenant",
                neo4j_password="test-password",
                azure_openai_endpoint="https://test.openai.azure.com/",
                azure_openai_key="test-key",
                core_api_port=80
            )
        
        errors = exc_info.value.errors()
        assert any("Port must be between 1024 and 65535" in str(error["ctx"]["reason"]) for error in errors)

    def test_environment_properties(self):
        """Test environment property methods."""
        dev_settings = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="test-password",
            azure_openai_endpoint="https://test.openai.azure.com/",
            azure_openai_key="test-key",
            environment="development"
        )
        
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False
        
        prod_settings = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="test-password",
            azure_openai_endpoint="https://test.openai.azure.com/",
            azure_openai_key="test-key",
            environment="production"
        )
        
        assert prod_settings.is_development is False
        assert prod_settings.is_production is True

    def test_production_validation(self):
        """Test production environment validation."""
        settings = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="test-password",
            azure_openai_endpoint="https://test.openai.azure.com/",
            azure_openai_key="test-key",
            environment="production"
        )
        
        # Should not raise an error for complete config
        settings.validate_required_for_environment()
        
        # Test with missing required field
        settings_incomplete = Settings(
            azure_tenant_id="test-tenant",
            neo4j_password="",  # Missing required field
            azure_openai_endpoint="https://test.openai.azure.com/",
            azure_openai_key="test-key",
            environment="production"
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            settings_incomplete.validate_required_for_environment()
        
        assert "Missing required configuration for production environment" in str(exc_info.value)


class TestConfigHelpers:
    """Test configuration helper functions."""

    def test_get_settings_caching(self):
        """Test that get_settings uses caching."""
        # Mock environment variables
        with patch.dict(os.environ, {
            "AZURE_TENANT_ID": "test-tenant",
            "NEO4J_PASSWORD": "test-password",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_KEY": "test-key"
        }):
            settings1 = get_settings()
            settings2 = get_settings()
            
            # Should return the same instance due to caching
            assert settings1 is settings2

    def test_get_settings_configuration_error(self):
        """Test get_settings with invalid configuration."""
        with patch.dict(os.environ, {}, clear=True):
            # Also clear the cache to ensure fresh Settings() creation
            from src.scaffolding.config import get_settings
            get_settings.cache_clear()
            with pytest.raises(ConfigurationError) as exc_info:
                get_settings()
            
            assert "Failed to load configuration" in str(exc_info.value)

    def test_create_env_template(self):
        """Test creation of .env.template file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock get_project_root to return temp directory
            with patch("src.scaffolding.config.get_project_root", return_value=Path(temp_dir)):
                create_env_template()
                
                template_file = Path(temp_dir) / ".env.template"
                assert template_file.exists()
                
                content = template_file.read_text(encoding="utf-8")
                
                # Check that template contains expected sections
                assert "# Azure Authentication" in content
                assert "AZURE_TENANT_ID=" in content
                assert "# Graph Database" in content
                assert "NEO4J_URI=" in content
                assert "# LLM Integration" in content
                assert "AZURE_OPENAI_ENDPOINT=" in content
                assert "# Service Bus" in content
                assert "SERVICE_BUS_URL=" in content


class TestEnvironmentVariableLoading:
    """Test loading configuration from environment variables."""

    def test_env_var_loading(self):
        """Test that environment variables are loaded correctly."""
        env_vars = {
            "AZURE_TENANT_ID": "env-tenant-id",
            "NEO4J_PASSWORD": "env-password",
            "AZURE_OPENAI_ENDPOINT": "https://env.openai.azure.com",
            "AZURE_OPENAI_KEY": "env-key",
            "LOG_LEVEL": "DEBUG",
            "ENVIRONMENT": "testing",
            "DEBUG_MODE": "true",
            "CORE_API_PORT": "8080"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.azure_tenant_id == "env-tenant-id"
            assert settings.neo4j_password == "env-password"
            assert settings.azure_openai_endpoint == "https://env.openai.azure.com/"
            assert settings.azure_openai_key == "env-key"
            assert settings.log_level == "DEBUG"
            assert settings.environment == "testing"
            assert settings.debug_mode is True
            assert settings.core_api_port == 8080

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive."""
        env_vars = {
            "azure_tenant_id": "lowercase-tenant",  # lowercase
            "NEO4J_PASSWORD": "test-password",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_KEY": "test-key"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.azure_tenant_id == "lowercase-tenant"