"""Tests for Service Bus data models."""

import json
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.simbuilder_servicebus.models import ConnectionConfig
from src.simbuilder_servicebus.models import DiscoveryStatusMessage
from src.simbuilder_servicebus.models import MessagePriority
from src.simbuilder_servicebus.models import MessageSchema
from src.simbuilder_servicebus.models import MessageType
from src.simbuilder_servicebus.models import ProgressMessage
from src.simbuilder_servicebus.models import SubscriptionConfig
from src.simbuilder_servicebus.models import TopicDefinition


class TestMessageType:
    """Test MessageType enumeration."""

    def test_message_type_values(self):
        """Test that all expected message types are defined."""
        expected_types = {
            "progress_update",
            "discovery_start",
            "discovery_complete",
            "discovery_error",
            "system_status",
        }

        actual_types = {mt.value for mt in MessageType}
        assert actual_types == expected_types

    def test_message_type_creation(self):
        """Test creating MessageType from string."""
        assert MessageType("progress_update") == MessageType.PROGRESS_UPDATE
        assert MessageType("system_status") == MessageType.SYSTEM_STATUS


class TestMessagePriority:
    """Test MessagePriority enumeration."""

    def test_priority_values(self):
        """Test that all expected priority levels are defined."""
        expected_priorities = {"low", "normal", "high", "critical"}
        actual_priorities = {mp.value for mp in MessagePriority}
        assert actual_priorities == expected_priorities

    def test_priority_creation(self):
        """Test creating MessagePriority from string."""
        assert MessagePriority("normal") == MessagePriority.NORMAL
        assert MessagePriority("critical") == MessagePriority.CRITICAL


class TestMessageSchema:
    """Test base MessageSchema model."""

    def test_message_schema_creation(self):
        """Test creating a valid MessageSchema."""
        message = MessageSchema(
            message_id="test-123",
            message_type=MessageType.SYSTEM_STATUS,
            source="test_service",
            data={"key": "value"},
        )

        assert message.message_id == "test-123"
        assert message.message_type == MessageType.SYSTEM_STATUS
        assert message.source == "test_service"
        assert message.data == {"key": "value"}
        assert message.priority == MessagePriority.NORMAL  # default
        assert message.session_id is None  # default
        assert isinstance(message.timestamp, datetime)

    def test_message_schema_with_session(self):
        """Test MessageSchema with session ID."""
        session_id = str(uuid4())
        message = MessageSchema(
            message_id="test-456",
            message_type=MessageType.DISCOVERY_START,
            session_id=session_id,
            source="discovery_agent",
            priority=MessagePriority.HIGH,
        )

        assert message.session_id == session_id
        assert message.priority == MessagePriority.HIGH

    def test_message_schema_validation_error(self):
        """Test MessageSchema validation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            MessageSchema(
                message_type=MessageType.SYSTEM_STATUS,
                # Missing message_id and source
            )

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "message_id" in error_fields
        assert "source" in error_fields

    def test_message_schema_json_serialization(self):
        """Test JSON serialization of MessageSchema."""
        timestamp = datetime.utcnow()
        message = MessageSchema(
            message_id="test-789",
            message_type=MessageType.PROGRESS_UPDATE,
            source="test_service",
            timestamp=timestamp,
            data={"progress": 50},
        )

        json_data = message.model_dump_json()
        parsed = json.loads(json_data)

        assert parsed["message_id"] == "test-789"
        assert parsed["message_type"] == "progress_update"
        assert parsed["source"] == "test_service"
        assert parsed["timestamp"] == timestamp.isoformat()
        assert parsed["data"] == {"progress": 50}


class TestProgressMessage:
    """Test ProgressMessage model."""

    def test_progress_message_creation(self):
        """Test creating a valid ProgressMessage."""
        message = ProgressMessage(
            message_id="progress-123",
            session_id="session-456",
            source="discovery_engine",
            operation="tenant_discovery",
            progress_percentage=75.5,
            current_step="Analyzing relationships",
        )

        assert message.message_type == MessageType.PROGRESS_UPDATE
        assert message.operation == "tenant_discovery"
        assert message.progress_percentage == 75.5
        assert message.current_step == "Analyzing relationships"

    def test_progress_message_with_steps(self):
        """Test ProgressMessage with step tracking."""
        message = ProgressMessage(
            message_id="progress-456",
            session_id="session-789",
            source="discovery_engine",
            operation="resource_enumeration",
            progress_percentage=40.0,
            current_step="Enumerating storage accounts",
            total_steps=10,
            current_step_number=4,
        )

        assert message.total_steps == 10
        assert message.current_step_number == 4

    def test_progress_percentage_validation(self):
        """Test progress percentage validation."""
        # Valid percentage
        message = ProgressMessage(
            message_id="test",
            source="test",
            operation="test",
            progress_percentage=50.0,
            current_step="test",
        )
        assert message.progress_percentage == 50.0

        # Invalid percentage - too low
        with pytest.raises(ValidationError):
            ProgressMessage(
                message_id="test",
                source="test",
                operation="test",
                progress_percentage=-10.0,
                current_step="test",
            )

        # Invalid percentage - too high
        with pytest.raises(ValidationError):
            ProgressMessage(
                message_id="test",
                source="test",
                operation="test",
                progress_percentage=150.0,
                current_step="test",
            )


class TestDiscoveryStatusMessage:
    """Test DiscoveryStatusMessage model."""

    def test_discovery_status_creation(self):
        """Test creating a valid DiscoveryStatusMessage."""
        message = DiscoveryStatusMessage(
            message_id="status-123",
            session_id="session-456",
            source="discovery_agent",
            tenant_id="tenant-789",
            subscription_id="sub-123",
            resources_discovered=150,
            relationships_mapped=75,
            errors_encountered=2,
            status="in_progress",
        )

        assert message.tenant_id == "tenant-789"
        assert message.subscription_id == "sub-123"
        assert message.resources_discovered == 150
        assert message.relationships_mapped == 75
        assert message.errors_encountered == 2
        assert message.status == "in_progress"

    def test_discovery_status_defaults(self):
        """Test DiscoveryStatusMessage with default values."""
        message = DiscoveryStatusMessage(
            message_id="status-456",
            source="discovery_agent",
            tenant_id="tenant-789",
            status="starting",
        )

        assert message.resources_discovered == 0
        assert message.relationships_mapped == 0
        assert message.errors_encountered == 0
        assert message.subscription_id is None


class TestTopicDefinition:
    """Test TopicDefinition model."""

    def test_topic_definition_creation(self):
        """Test creating a valid TopicDefinition."""
        topic = TopicDefinition(
            name="test_topic",
            subject_pattern="test.*",
            description="Test topic for unit tests",
            message_types=[MessageType.SYSTEM_STATUS, MessageType.PROGRESS_UPDATE],
            max_age_seconds=1800,
            max_messages=5000,
        )

        assert topic.name == "test_topic"
        assert topic.subject_pattern == "test.*"
        assert topic.description == "Test topic for unit tests"
        assert len(topic.message_types) == 2
        assert MessageType.SYSTEM_STATUS in topic.message_types
        assert topic.max_age_seconds == 1800
        assert topic.max_messages == 5000
        assert topic.retention_policy == "workqueue"  # default

    def test_topic_definition_defaults(self):
        """Test TopicDefinition with default values."""
        topic = TopicDefinition(
            name="minimal_topic",
            subject_pattern="minimal.*",
            description="Minimal topic",
            message_types=[MessageType.SYSTEM_STATUS],
        )

        assert topic.retention_policy == "workqueue"
        assert topic.max_age_seconds == 3600
        assert topic.max_messages == 10000
        assert topic.replicas == 1


class TestSubscriptionConfig:
    """Test SubscriptionConfig model."""

    def test_subscription_config_creation(self):
        """Test creating a valid SubscriptionConfig."""
        config = SubscriptionConfig(
            name="test_subscription",
            topic="test_topic",
            subject_filter="test.specific.*",
            queue_group="test_group",
            durable=True,
            auto_ack=False,
            max_pending=500,
            ack_wait_seconds=60,
        )

        assert config.name == "test_subscription"
        assert config.topic == "test_topic"
        assert config.subject_filter == "test.specific.*"
        assert config.queue_group == "test_group"
        assert config.durable is True
        assert config.auto_ack is False
        assert config.max_pending == 500
        assert config.ack_wait_seconds == 60

    def test_subscription_config_defaults(self):
        """Test SubscriptionConfig with default values."""
        config = SubscriptionConfig(name="default_subscription", topic="default_topic")

        assert config.subject_filter is None
        assert config.queue_group is None
        assert config.durable is True
        assert config.auto_ack is False
        assert config.max_pending == 1000
        assert config.ack_wait_seconds == 30


class TestConnectionConfig:
    """Test ConnectionConfig model."""

    def test_connection_config_creation(self):
        """Test creating a valid ConnectionConfig."""
        config = ConnectionConfig(
            servers=["nats://localhost:4222", "nats://backup:4222"],
            cluster_id="test_cluster",
            client_id="test_client",
            max_reconnect_attempts=5,
            reconnect_time_wait=3,
            ping_interval=60,
        )

        assert config.servers == ["nats://localhost:4222", "nats://backup:4222"]
        assert config.cluster_id == "test_cluster"
        assert config.client_id == "test_client"
        assert config.max_reconnect_attempts == 5
        assert config.reconnect_time_wait == 3
        assert config.ping_interval == 60

    def test_connection_config_defaults(self):
        """Test ConnectionConfig with default values."""
        config = ConnectionConfig(
            servers=["nats://localhost:4222"], cluster_id="test_cluster", client_id="test_client"
        )

        assert config.max_reconnect_attempts == 10
        assert config.reconnect_time_wait == 2
        assert config.ping_interval == 120
        assert config.max_outstanding == 65536

    def test_connection_config_validation(self):
        """Test ConnectionConfig validation."""
        # Test assignment validation is enabled
        config = ConnectionConfig(
            servers=["nats://localhost:4222"], cluster_id="test_cluster", client_id="test_client"
        )

        # Should allow updating valid values
        config.max_reconnect_attempts = 15
        assert config.max_reconnect_attempts == 15
