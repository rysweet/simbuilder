"""NATS JetStream client for Service Bus messaging."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import nats
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig, StreamConfig, StreamInfo
from nats.js.errors import NotFoundError

from src.scaffolding.config import get_settings
from src.scaffolding.logging import LoggingMixin

from .models import (
    ConnectionConfig,
    MessageSchema,
    SubscriptionConfig,
    TopicDefinition,
)


class ServiceBusClient(LoggingMixin):
    """NATS JetStream client for SimBuilder messaging."""

    def __init__(self, connection_config: Optional[ConnectionConfig] = None):
        """Initialize the Service Bus client.
        
        Args:
            connection_config: Optional connection configuration.
                              If None, loads from scaffolding settings.
        """
        super().__init__()
        self.settings = get_settings()
        
        if connection_config:
            self.connection_config = connection_config
        else:
            # Create connection config from scaffolding settings
            self.connection_config = ConnectionConfig(
                servers=[self.settings.service_bus_url],
                cluster_id=self.settings.service_bus_cluster_id,
                client_id=f"simbuilder-{uuid.uuid4().hex[:8]}",
            )
        
        self._nats: Optional[NATS] = None
        self._js: Optional[JetStreamContext] = None
        self._connected = False
        self._subscriptions: Dict[str, Any] = {}
        self._streams: Dict[str, StreamInfo] = {}

    async def connect(self) -> None:
        """Connect to NATS JetStream."""
        if self._connected:
            return

        try:
            self.logger.info("Connecting to NATS JetStream", servers=self.connection_config.servers)
            
            self._nats = await nats.connect(
                servers=self.connection_config.servers,
                name=self.connection_config.client_id,
                max_reconnect_attempts=self.connection_config.max_reconnect_attempts,
                reconnect_time_wait=self.connection_config.reconnect_time_wait,
                ping_interval=self.connection_config.ping_interval,
                max_outstanding=self.connection_config.max_outstanding,
                error_cb=self._error_callback,
                disconnected_cb=self._disconnected_callback,
                reconnected_cb=self._reconnected_callback,
            )
            
            self._js = self._nats.jetstream()
            self._connected = True
            
            self.logger.info("Successfully connected to NATS JetStream")
            
        except Exception as e:
            self.log_error(e, {"operation": "connect"})
            raise

    async def disconnect(self) -> None:
        """Disconnect from NATS JetStream."""
        if not self._connected:
            return

        try:
            self.logger.info("Disconnecting from NATS JetStream")
            
            # Close all subscriptions
            for sub_name, subscription in self._subscriptions.items():
                try:
                    await subscription.unsubscribe()
                except Exception as e:
                    self.log_error(e, {"operation": "unsubscribe", "subscription": sub_name})
            
            self._subscriptions.clear()
            
            if self._nats:
                await self._nats.close()
                
            self._nats = None
            self._js = None
            self._connected = False
            
            self.logger.info("Disconnected from NATS JetStream")
            
        except Exception as e:
            self.log_error(e, {"operation": "disconnect"})

    async def create_stream(self, topic: TopicDefinition) -> StreamInfo:
        """Create or update a JetStream stream for a topic.
        
        Args:
            topic: Topic definition with stream configuration
            
        Returns:
            Stream information
        """
        if not self._js:
            raise RuntimeError("Not connected to JetStream")

        try:
            self.logger.info("Creating/updating stream", topic=topic.name)
            
            stream_config = StreamConfig(
                name=topic.name,
                subjects=[topic.subject_pattern],
                retention=topic.retention_policy,
                max_age=topic.max_age_seconds,
                max_msgs=topic.max_messages,
                replicas=topic.replicas,
            )
            
            try:
                # Try to update existing stream
                stream_info = await self._js.update_stream(stream_config)
                self.logger.info("Updated existing stream", stream=topic.name)
            except NotFoundError:
                # Create new stream
                stream_info = await self._js.add_stream(stream_config)
                self.logger.info("Created new stream", stream=topic.name)
            
            self._streams[topic.name] = stream_info
            return stream_info
            
        except Exception as e:
            self.log_error(e, {"operation": "create_stream", "topic": topic.name})
            raise

    async def publish(
        self, 
        subject: str, 
        message: MessageSchema,
        timeout: float = 10.0
    ) -> str:
        """Publish a message to a subject.
        
        Args:
            subject: NATS subject to publish to
            message: Message to publish
            timeout: Publish timeout in seconds
            
        Returns:
            Message ID from JetStream acknowledgment
        """
        if not self._js:
            raise RuntimeError("Not connected to JetStream")

        try:
            # Serialize message to JSON
            message_data = message.model_dump_json().encode('utf-8')
            
            self.logger.debug(
                "Publishing message",
                subject=subject,
                message_id=message.message_id,
                message_type=message.message_type
            )
            
            # Publish with acknowledgment
            ack = await self._js.publish(
                subject=subject,
                payload=message_data,
                timeout=timeout,
                headers={"message-id": message.message_id}
            )
            
            self.logger.info(
                "Message published successfully",
                subject=subject,
                message_id=message.message_id,
                stream=ack.stream,
                sequence=ack.seq
            )
            
            return message.message_id
            
        except Exception as e:
            self.log_error(e, {
                "operation": "publish",
                "subject": subject,
                "message_id": getattr(message, 'message_id', 'unknown')
            })
            raise

    async def subscribe(
        self,
        config: SubscriptionConfig,
        message_handler: Callable[[MessageSchema], None],
        error_handler: Optional[Callable[[Exception], None]] = None
    ) -> str:
        """Subscribe to messages on a topic.
        
        Args:
            config: Subscription configuration
            message_handler: Callback function for processing messages
            error_handler: Optional error handling callback
            
        Returns:
            Subscription ID
        """
        if not self._js:
            raise RuntimeError("Not connected to JetStream")

        try:
            self.logger.info("Creating subscription", subscription=config.name)
            
            async def msg_handler(msg):
                try:
                    # Parse message
                    message_data = json.loads(msg.data.decode('utf-8'))
                    message = MessageSchema(**message_data)
                    
                    self.logger.debug(
                        "Received message",
                        subject=msg.subject,
                        message_id=message.message_id,
                        message_type=message.message_type
                    )
                    
                    # Process message
                    await message_handler(message)
                    
                    # Acknowledge message if not auto-ack
                    if not config.auto_ack:
                        await msg.ack()
                        
                except Exception as e:
                    self.log_error(e, {
                        "operation": "message_processing",
                        "subject": msg.subject,
                        "subscription": config.name
                    })
                    
                    if error_handler:
                        await error_handler(e)
                    
                    # Negative acknowledgment for retry
                    if not config.auto_ack:
                        await msg.nak()

            # Create consumer configuration
            consumer_config = ConsumerConfig(
                durable_name=config.name if config.durable else None,
                deliver_group=config.queue_group,
                ack_wait=config.ack_wait_seconds,
                max_deliver=3,  # Retry up to 3 times
                filter_subject=config.subject_filter or f"{config.topic}.*",
            )
            
            # Subscribe
            subscription = await self._js.subscribe(
                subject=config.subject_filter or f"{config.topic}.*",
                cb=msg_handler,
                config=consumer_config,
                manual_ack=not config.auto_ack,
                pending_msgs_limit=config.max_pending,
            )
            
            subscription_id = f"{config.name}-{uuid.uuid4().hex[:8]}"
            self._subscriptions[subscription_id] = subscription
            
            self.logger.info(
                "Subscription created successfully",
                subscription=config.name,
                subscription_id=subscription_id
            )
            
            return subscription_id
            
        except Exception as e:
            self.log_error(e, {"operation": "subscribe", "subscription": config.name})
            raise

    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from a topic.
        
        Args:
            subscription_id: Subscription ID returned from subscribe()
        """
        if subscription_id not in self._subscriptions:
            self.logger.warning("Subscription not found", subscription_id=subscription_id)
            return

        try:
            subscription = self._subscriptions[subscription_id]
            await subscription.unsubscribe()
            del self._subscriptions[subscription_id]
            
            self.logger.info("Unsubscribed successfully", subscription_id=subscription_id)
            
        except Exception as e:
            self.log_error(e, {"operation": "unsubscribe", "subscription_id": subscription_id})

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the connection.
        
        Returns:
            Health check status information
        """
        health_status = {
            "connected": self._connected,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": self.connection_config.client_id,
            "servers": self.connection_config.servers,
        }

        if self._connected and self._nats:
            try:
                # Test connection with RTT
                rtt = await self._nats.rtt()
                health_status.update({
                    "rtt_ms": round(rtt * 1000, 2),
                    "is_connected": self._nats.is_connected,
                    "server_info": self._nats.connected_server_version,
                    "active_subscriptions": len(self._subscriptions),
                    "active_streams": len(self._streams),
                })
            except Exception as e:
                health_status.update({
                    "error": str(e),
                    "status": "unhealthy"
                })

        return health_status

    # Event callbacks
    async def _error_callback(self, error: Exception) -> None:
        """Handle NATS connection errors."""
        self.log_error(error, {"source": "nats_error_callback"})

    async def _disconnected_callback(self) -> None:
        """Handle NATS disconnection."""
        self._connected = False
        self.logger.warning("NATS connection lost")

    async def _reconnected_callback(self) -> None:
        """Handle NATS reconnection."""
        self._connected = True
        self.logger.info("NATS connection restored")

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()