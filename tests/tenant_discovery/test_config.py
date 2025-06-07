"""Tests for tenant_discovery.config module."""

import os
import uuid
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from src.tenant_discovery.cli import app
from src.tenant_discovery.config import LogLevel, TenantDiscoverySettings, get_td_settings


class TestTenantDiscoverySettings:
    """Test cases for TenantDiscoverySettings."""

    def test_valid_configuration(self):
        """Test creating settings with valid values."""
        # Generate valid UUIDs for testing
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        
        settings = TenantDiscoverySettings(
            azure_tenant_id=tenant_id,
            azure_client_id=client_id,
            azure_client_secret="test-secret-123",
            subscription_id=subscription_id,
            _env_file=None,
        )
        
        assert settings.azure_tenant_id == tenant_id
        assert settings.azure_client_id == client_id
        assert settings.azure_client_secret == "test-secret-123"
        assert settings.subscription_id == subscription_id
        assert settings.graph_db_url == "bolt://localhost:30000"
        assert settings.service_bus_url == "nats://localhost:30002"
        assert settings.log_level == LogLevel.INFO

    def test_custom_defaults(self):
        """Test settings with custom default values."""
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        
        settings = TenantDiscoverySettings(
            azure_tenant_id=tenant_id,
            azure_client_id=client_id,
            azure_client_secret="test-secret",
            subscription_id=subscription_id,
            graph_db_url="bolt://remote:7687",
            service_bus_url="nats://remote:4222",
            log_level=LogLevel.DEBUG,
            _env_file=None,
        )
        
        assert settings.graph_db_url == "bolt://remote:7687"
        assert settings.service_bus_url == "nats://remote:4222"
        assert settings.log_level == LogLevel.DEBUG

    def test_invalid_uuid_format(self):
        """Test validation error for invalid UUID format."""
        with pytest.raises(ValidationError) as exc_info:
            TenantDiscoverySettings(
                azure_tenant_id="not-a-uuid",
                azure_client_id=str(uuid.uuid4()),
                azure_client_secret="test-secret",
                subscription_id=str(uuid.uuid4()),
                _env_file=None,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "azure_tenant_id" in str(errors[0]["loc"])
        assert "UUID format" in errors[0]["msg"]

    def test_multiple_invalid_uuids(self):
        """Test validation errors for multiple invalid UUIDs."""
        with pytest.raises(ValidationError) as exc_info:
            TenantDiscoverySettings(
                azure_tenant_id="not-a-uuid",
                azure_client_id="also-not-a-uuid",
                azure_client_secret="test-secret",
                subscription_id="still-not-a-uuid",
                _env_file=None,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 3  # Three UUID validation errors
        error_fields = {str(error["loc"]) for error in errors}
        assert "('azure_tenant_id',)" in error_fields
        assert "('azure_client_id',)" in error_fields
        assert "('subscription_id',)" in error_fields

    def test_invalid_graph_db_url_scheme(self):
        """Test validation error for invalid graph DB URL scheme."""
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        
        with pytest.raises(ValidationError) as exc_info:
            TenantDiscoverySettings(
                azure_tenant_id=tenant_id,
                azure_client_id=client_id,
                azure_client_secret="test-secret",
                subscription_id=subscription_id,
                graph_db_url="http://localhost:7687",
                _env_file=None,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "graph_db_url" in str(errors[0]["loc"])
        assert "valid Neo4j scheme" in errors[0]["msg"]

    def test_valid_graph_db_url_schemes(self):
        """Test valid Neo4j URL schemes."""
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        
        valid_schemes = [
            "bolt://localhost:7687",
            "bolt+s://localhost:7687",
            "bolt+ssc://localhost:7687",
            "neo4j://localhost:7687",
            "neo4j+s://localhost:7687",
            "neo4j+ssc://localhost:7687",
        ]
        
        for url in valid_schemes:
            settings = TenantDiscoverySettings(
                azure_tenant_id=tenant_id,
                azure_client_id=client_id,
                azure_client_secret="test-secret",
                subscription_id=subscription_id,
                graph_db_url=url,
                _env_file=None,
            )
            assert settings.graph_db_url == url

    def test_invalid_service_bus_url_scheme(self):
        """Test validation error for invalid service bus URL scheme."""
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        
        with pytest.raises(ValidationError) as exc_info:
            TenantDiscoverySettings(
                azure_tenant_id=tenant_id,
                azure_client_id=client_id,
                azure_client_secret="test-secret",
                subscription_id=subscription_id,
                service_bus_url="http://localhost:4222",
                _env_file=None,
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "service_bus_url" in str(errors[0]["loc"])
        assert "nats://" in errors[0]["msg"]

    def test_valid_service_bus_url_schemes(self):
        """Test valid NATS URL schemes."""
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        
        valid_schemes = [
            "nats://localhost:4222",
            "nats+tls://localhost:4222",
        ]
        
        for url in valid_schemes:
            settings = TenantDiscoverySettings(
                azure_tenant_id=tenant_id,
                azure_client_id=client_id,
                azure_client_secret="test-secret",
                subscription_id=subscription_id,
                service_bus_url=url,
                _env_file=None,
            )
            assert settings.service_bus_url == url

    def test_log_level_enum(self):
        """Test log level enum validation."""
        tenant_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        subscription_id = str(uuid.uuid4())
        
        for level in LogLevel:
            settings = TenantDiscoverySettings(
                azure_tenant_id=tenant_id,
                azure_client_id=client_id,
                azure_client_secret="test-secret",
                subscription_id=subscription_id,
                log_level=level,
                _env_file=None,
            )
            assert settings.log_level == level

    @patch.dict(os.environ, {
        "TD_AZURE_TENANT_ID": "12345678-1234-1234-1234-123456789012",
        "TD_AZURE_CLIENT_ID": "87654321-4321-4321-4321-210987654321",
        "TD_AZURE_CLIENT_SECRET": "env-secret-123",
        "TD_SUBSCRIPTION_ID": "11111111-2222-3333-4444-555555555555",
        "TD_LOG_LEVEL": "DEBUG",
    }, clear=True)
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        # Clear the cache to ensure fresh loading
        get_td_settings.cache_clear()
        
        settings = get_td_settings()
        
        assert settings.azure_tenant_id == "12345678-1234-1234-1234-123456789012"
        assert settings.azure_client_id == "87654321-4321-4321-4321-210987654321"
        assert settings.azure_client_secret == "env-secret-123"
        assert settings.subscription_id == "11111111-2222-3333-4444-555555555555"
        assert settings.log_level == LogLevel.DEBUG


class TestGetTdSettings:
    """Test cases for get_td_settings function."""

    def setUp(self):
        """Clear cache before each test."""
        get_td_settings.cache_clear()

    def test_singleton_behavior(self):
        """Test that get_td_settings returns the same instance."""
        # Clear cache first
        get_td_settings.cache_clear()
        
        with patch.dict(os.environ, {
            "TD_AZURE_TENANT_ID": str(uuid.uuid4()),
            "TD_AZURE_CLIENT_ID": str(uuid.uuid4()),
            "TD_AZURE_CLIENT_SECRET": "test-secret",
            "TD_SUBSCRIPTION_ID": str(uuid.uuid4()),
        }, clear=True):
            settings1 = get_td_settings()
            settings2 = get_td_settings()
            
            assert settings1 is settings2


class TestTenantDiscoveryCLI:
    """Test cases for the tenant discovery CLI."""

    def setUp(self):
        """Clear cache before each test."""
        get_td_settings.cache_clear()

    @patch.dict(os.environ, {
        "TD_AZURE_TENANT_ID": "12345678-1234-1234-1234-123456789012",
        "TD_AZURE_CLIENT_ID": "87654321-4321-4321-4321-210987654321",
        "TD_AZURE_CLIENT_SECRET": "test-secret-from-env",
        "TD_SUBSCRIPTION_ID": "11111111-2222-3333-4444-555555555555",
    }, clear=True)
    def test_info_command_success(self):
        """Test the info command with valid configuration."""
        get_td_settings.cache_clear()
        runner = CliRunner()
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "Tenant Discovery Configuration" in result.stdout
        assert "***" in result.stdout  # Masked secret
        assert "test-secret-from-env" not in result.stdout  # Secret should be masked
        assert "Configuration loaded successfully" in result.stdout

    @patch.dict(os.environ, {
        "TD_AZURE_TENANT_ID": "invalid-uuid",
        "TD_AZURE_CLIENT_ID": "also-invalid",
        "TD_AZURE_CLIENT_SECRET": "test-secret",
        "TD_SUBSCRIPTION_ID": "still-invalid",
    }, clear=True)
    def test_info_command_validation_error(self):
        """Test the info command with invalid configuration."""
        get_td_settings.cache_clear()
        runner = CliRunner()
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 1
        assert "Configuration validation failed" in result.stdout

    @patch.dict(os.environ, {
        "TD_AZURE_TENANT_ID": "12345678-1234-1234-1234-123456789012",
        "TD_AZURE_CLIENT_ID": "87654321-4321-4321-4321-210987654321",
        "TD_AZURE_CLIENT_SECRET": "test-secret-from-env",
        "TD_SUBSCRIPTION_ID": "11111111-2222-3333-4444-555555555555",
    }, clear=True)
    def test_check_command_success(self):
        """Test the check command with valid configuration."""
        get_td_settings.cache_clear()
        runner = CliRunner()
        result = runner.invoke(app, ["check"])
        
        assert result.exit_code == 0
        assert "Validating Tenant Discovery configuration" in result.stdout
        assert "All configuration checks passed" in result.stdout

    @patch.dict(os.environ, {
        "TD_AZURE_TENANT_ID": "invalid-uuid",
        "TD_AZURE_CLIENT_ID": "also-invalid",
        "TD_AZURE_CLIENT_SECRET": "test-secret",
        "TD_SUBSCRIPTION_ID": "still-invalid",
    }, clear=True)
    def test_check_command_validation_error(self):
        """Test the check command with invalid configuration."""
        get_td_settings.cache_clear()
        runner = CliRunner()
        result = runner.invoke(app, ["check"])
        
        assert result.exit_code == 1
        assert "Configuration validation failed" in result.stdout

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Tenant Discovery Configuration CLI" in result.stdout
        assert "info" in result.stdout
        assert "check" in result.stdout