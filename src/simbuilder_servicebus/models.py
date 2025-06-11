"""Data models for Service Bus messaging."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class MessageType(str, Enum):
    """Message type enumeration."""

    PROGRESS_UPDATE = "progress_update"
    DISCOVERY_START = "discovery_start"
    DISCOVERY_COMPLETE = "discovery_complete"
    DISCOVERY_ERROR = "discovery_error"
    SYSTEM_STATUS = "system_status"


class MessagePriority(str, Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MessageSchema(BaseModel):
    """Base message schema for all Service Bus messages."""

    message_id: str = Field(..., description="Unique message identifier")
    message_type: MessageType = Field(..., description="Type of message")
    session_id: str | None = Field(None, description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    priority: MessagePriority = Field(MessagePriority.NORMAL, description="Message priority")
    source: str = Field(..., description="Source service/component")
    data: dict[str, Any] = Field(default_factory=dict, description="Message payload")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }


class ProgressMessage(MessageSchema):
    """Progress update message for long-running operations."""

    message_type: MessageType = Field(MessageType.PROGRESS_UPDATE, description="Fixed message type")
    operation: str = Field(..., description="Operation being tracked")
    progress_percentage: float | None = Field(
        None, ge=0.0, le=100.0, description="Completion percentage (None for errors)"
    )
    current_step: str = Field(..., description="Current operation step")
    total_steps: int | None = Field(None, description="Total number of steps")
    current_step_number: int | None = Field(None, description="Current step number")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")
    details: str | None = Field(None, description="Additional progress details")


class DiscoveryStatusMessage(MessageSchema):
    """Discovery session status message."""

    message_type: MessageType = Field(MessageType.SYSTEM_STATUS, description="Fixed message type")
    tenant_id: str = Field(..., description="Azure tenant ID")
    subscription_id: str | None = Field(None, description="Azure subscription ID")
    resources_discovered: int = Field(0, description="Number of resources discovered")
    relationships_mapped: int = Field(0, description="Number of relationships mapped")
    errors_encountered: int = Field(0, description="Number of errors encountered")
    status: str = Field(..., description="Current discovery status")


class TopicDefinition(BaseModel):
    """Topic configuration and routing definition."""

    name: str = Field(..., description="Topic name")
    subject_pattern: str = Field(..., description="NATS subject pattern")
    description: str = Field(..., description="Topic description")
    message_types: list[MessageType] = Field(..., description="Supported message types")
    retention_policy: str = Field("workqueue", description="Message retention policy")
    max_age_seconds: int = Field(3600, description="Maximum message age in seconds")
    max_messages: int = Field(10000, description="Maximum number of messages")
    replicas: int = Field(1, description="Number of replicas")

    class Config:
        """Pydantic configuration."""

        use_enum_values = False


class SubscriptionConfig(BaseModel):
    """Subscription configuration for message consumers."""

    name: str = Field(..., description="Subscription name")
    topic: str = Field(..., description="Topic to subscribe to")
    subject_filter: str | None = Field(None, description="Subject filter pattern")
    queue_group: str | None = Field(None, description="Queue group for load balancing")
    durable: bool = Field(True, description="Whether subscription is durable")
    auto_ack: bool = Field(False, description="Whether to auto-acknowledge messages")
    max_pending: int = Field(1000, description="Maximum pending messages")
    ack_wait_seconds: int = Field(30, description="Acknowledgment wait timeout")


class ConnectionConfig(BaseModel):
    """NATS connection configuration."""

    servers: list[str] = Field(..., description="NATS server URLs")
    cluster_id: str = Field(..., description="NATS cluster identifier")
    client_id: str = Field(..., description="Client identifier")
    max_reconnect_attempts: int = Field(10, description="Maximum reconnection attempts")
    reconnect_time_wait: int = Field(2, description="Reconnection wait time in seconds")
    ping_interval: int = Field(120, description="Ping interval in seconds")
    max_outstanding: int = Field(65536, description="Maximum outstanding messages")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True
