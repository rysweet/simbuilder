"""Topic definitions and routing for Service Bus messaging."""


from .models import MessageType
from .models import TopicDefinition


class TopicManager:
    """Manages topic definitions and routing for SimBuilder messaging."""

    # Predefined topic definitions
    TOPICS: dict[str, TopicDefinition] = {
        "tenant_discovery": TopicDefinition(
            name="tenant_discovery",
            subject_pattern="tenant.discovery.*",
            description="Tenant discovery progress and status updates",
            message_types=[
                MessageType.DISCOVERY_START,
                MessageType.DISCOVERY_COMPLETE,
                MessageType.DISCOVERY_ERROR,
                MessageType.PROGRESS_UPDATE,
            ],
            retention_policy="workqueue",
            max_age_seconds=7200,  # 2 hours
            max_messages=50000,
            replicas=1,
        ),

        "system_events": TopicDefinition(
            name="system_events",
            subject_pattern="system.*",
            description="System-wide events and status messages",
            message_types=[
                MessageType.SYSTEM_STATUS,
            ],
            retention_policy="limits",
            max_age_seconds=3600,  # 1 hour
            max_messages=10000,
            replicas=1,
        ),

        "simulation_events": TopicDefinition(
            name="simulation_events",
            subject_pattern="simulation.*",
            description="Simulation lifecycle and progress events",
            message_types=[
                MessageType.PROGRESS_UPDATE,
                MessageType.SYSTEM_STATUS,
            ],
            retention_policy="workqueue",
            max_age_seconds=14400,  # 4 hours
            max_messages=100000,
            replicas=1,
        ),
    }

    @classmethod
    def get_topic(cls, name: str) -> TopicDefinition:
        """Get a topic definition by name.

        Args:
            name: Topic name

        Returns:
            Topic definition

        Raises:
            KeyError: If topic not found
        """
        if name not in cls.TOPICS:
            raise KeyError(f"Topic '{name}' not found")
        return cls.TOPICS[name]

    @classmethod
    def get_all_topics(cls) -> list[TopicDefinition]:
        """Get all topic definitions.

        Returns:
            List of all topic definitions
        """
        return list(cls.TOPICS.values())

    @classmethod
    def get_subject_for_discovery(cls, session_id: str, event_type: str) -> str:
        """Generate a subject for tenant discovery events.

        Args:
            session_id: Discovery session ID
            event_type: Type of discovery event (start, progress, complete, error)

        Returns:
            NATS subject string
        """
        return f"tenant.discovery.{session_id}.{event_type}"

    @classmethod
    def get_subject_for_simulation(cls, simulation_id: str, event_type: str) -> str:
        """Generate a subject for simulation events.

        Args:
            simulation_id: Simulation ID
            event_type: Type of simulation event

        Returns:
            NATS subject string
        """
        return f"simulation.{simulation_id}.{event_type}"

    @classmethod
    def get_subject_for_system(cls, component: str, event_type: str) -> str:
        """Generate a subject for system events.

        Args:
            component: System component name
            event_type: Type of system event

        Returns:
            NATS subject string
        """
        return f"system.{component}.{event_type}"

    @classmethod
    def add_custom_topic(cls, topic: TopicDefinition) -> None:
        """Add a custom topic definition.

        Args:
            topic: Topic definition to add
        """
        cls.TOPICS[topic.name] = topic

    @classmethod
    def remove_topic(cls, name: str) -> bool:
        """Remove a topic definition.

        Args:
            name: Topic name to remove

        Returns:
            True if topic was removed, False if not found
        """
        if name in cls.TOPICS:
            del cls.TOPICS[name]
            return True
        return False

    @classmethod
    def validate_subject(cls, subject: str) -> bool:
        """Validate that a subject matches a known topic pattern.

        Args:
            subject: NATS subject to validate

        Returns:
            True if subject matches a known topic pattern
        """
        for topic in cls.TOPICS.values():
            # Simple pattern matching - convert NATS wildcard to regex-like
            pattern = topic.subject_pattern.replace("*", "")
            if subject.startswith(pattern):
                return True
        return False

    @classmethod
    def get_topic_for_subject(cls, subject: str) -> TopicDefinition | None:
        """Find the topic definition that matches a subject.

        Args:
            subject: NATS subject

        Returns:
            Matching topic definition, or None if no match
        """
        for topic in cls.TOPICS.values():
            # Simple pattern matching - convert NATS wildcard to regex-like
            pattern = topic.subject_pattern.replace("*", "")
            if subject.startswith(pattern):
                return topic
        return None


# Convenience functions for common subject patterns
def discovery_subject(session_id: str, event_type: str) -> str:
    """Generate tenant discovery subject."""
    return TopicManager.get_subject_for_discovery(session_id, event_type)


def simulation_subject(simulation_id: str, event_type: str) -> str:
    """Generate simulation subject."""
    return TopicManager.get_subject_for_simulation(simulation_id, event_type)


def system_subject(component: str, event_type: str) -> str:
    """Generate system subject."""
    return TopicManager.get_subject_for_system(component, event_type)
