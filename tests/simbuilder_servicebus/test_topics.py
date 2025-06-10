"""Tests for Service Bus topic management."""

import pytest

from src.simbuilder_servicebus.models import MessageType
from src.simbuilder_servicebus.models import TopicDefinition
from src.simbuilder_servicebus.topics import TopicManager
from src.simbuilder_servicebus.topics import discovery_subject
from src.simbuilder_servicebus.topics import simulation_subject
from src.simbuilder_servicebus.topics import system_subject


class TestTopicManager:
    """Test TopicManager functionality."""

    def test_predefined_topics_exist(self):
        """Test that all expected predefined topics exist."""
        expected_topics = {"tenant_discovery", "system_events", "simulation_events"}
        actual_topics = set(TopicManager.TOPICS.keys())
        assert expected_topics.issubset(actual_topics)

    def test_get_topic_success(self):
        """Test getting an existing topic."""
        topic = TopicManager.get_topic("tenant_discovery")

        assert isinstance(topic, TopicDefinition)
        assert topic.name == "tenant_discovery"
        assert topic.subject_pattern == "tenant.discovery.*"
        assert MessageType.DISCOVERY_START in topic.message_types
        assert MessageType.PROGRESS_UPDATE in topic.message_types

    def test_get_topic_not_found(self):
        """Test getting a non-existent topic raises KeyError."""
        with pytest.raises(KeyError, match="Topic 'nonexistent' not found"):
            TopicManager.get_topic("nonexistent")

    def test_get_all_topics(self):
        """Test getting all topic definitions."""
        topics = TopicManager.get_all_topics()

        assert isinstance(topics, list)
        assert len(topics) >= 3  # At least the predefined ones
        assert all(isinstance(topic, TopicDefinition) for topic in topics)

        # Check that all predefined topics are included
        topic_names = {topic.name for topic in topics}
        expected_names = {"tenant_discovery", "system_events", "simulation_events"}
        assert expected_names.issubset(topic_names)

    def test_tenant_discovery_topic_config(self):
        """Test tenant discovery topic configuration."""
        topic = TopicManager.get_topic("tenant_discovery")

        assert topic.subject_pattern == "tenant.discovery.*"
        assert topic.retention_policy == "workqueue"
        assert topic.max_age_seconds == 7200  # 2 hours
        assert topic.max_messages == 50000

        expected_message_types = {
            MessageType.DISCOVERY_START,
            MessageType.DISCOVERY_COMPLETE,
            MessageType.DISCOVERY_ERROR,
            MessageType.PROGRESS_UPDATE,
        }
        assert set(topic.message_types) == expected_message_types

    def test_system_events_topic_config(self):
        """Test system events topic configuration."""
        topic = TopicManager.get_topic("system_events")

        assert topic.subject_pattern == "system.*"
        assert topic.retention_policy == "limits"
        assert topic.max_age_seconds == 3600  # 1 hour
        assert topic.max_messages == 10000
        assert MessageType.SYSTEM_STATUS in topic.message_types

    def test_simulation_events_topic_config(self):
        """Test simulation events topic configuration."""
        topic = TopicManager.get_topic("simulation_events")

        assert topic.subject_pattern == "simulation.*"
        assert topic.retention_policy == "workqueue"
        assert topic.max_age_seconds == 14400  # 4 hours
        assert topic.max_messages == 100000

        expected_message_types = {
            MessageType.PROGRESS_UPDATE,
            MessageType.SYSTEM_STATUS,
        }
        assert set(topic.message_types) == expected_message_types


class TestSubjectGeneration:
    """Test subject pattern generation methods."""

    def test_get_subject_for_discovery(self):
        """Test discovery subject generation."""
        session_id = "session-123"
        event_type = "progress"

        subject = TopicManager.get_subject_for_discovery(session_id, event_type)
        assert subject == "tenant.discovery.session-123.progress"

    def test_get_subject_for_simulation(self):
        """Test simulation subject generation."""
        simulation_id = "sim-456"
        event_type = "status"

        subject = TopicManager.get_subject_for_simulation(simulation_id, event_type)
        assert subject == "simulation.sim-456.status"

    def test_get_subject_for_system(self):
        """Test system subject generation."""
        component = "graph_db"
        event_type = "health"

        subject = TopicManager.get_subject_for_system(component, event_type)
        assert subject == "system.graph_db.health"


class TestCustomTopics:
    """Test custom topic management."""

    def test_add_custom_topic(self):
        """Test adding a custom topic."""
        custom_topic = TopicDefinition(
            name="custom_test_topic",
            subject_pattern="custom.test.*",
            description="Custom test topic",
            message_types=[MessageType.SYSTEM_STATUS],
            max_age_seconds=600,
            max_messages=1000,
        )

        # Store original topics for cleanup
        original_topics = TopicManager.TOPICS.copy()

        try:
            TopicManager.add_custom_topic(custom_topic)

            # Verify topic was added
            assert "custom_test_topic" in TopicManager.TOPICS
            retrieved_topic = TopicManager.get_topic("custom_test_topic")
            assert retrieved_topic.name == "custom_test_topic"
            assert retrieved_topic.subject_pattern == "custom.test.*"
            assert retrieved_topic.max_age_seconds == 600

        finally:
            # Cleanup - restore original topics
            TopicManager.TOPICS = original_topics

    def test_remove_topic_success(self):
        """Test removing an existing topic."""
        # Add a test topic first
        test_topic = TopicDefinition(
            name="removable_topic",
            subject_pattern="removable.*",
            description="Topic to be removed",
            message_types=[MessageType.SYSTEM_STATUS],
        )

        original_topics = TopicManager.TOPICS.copy()

        try:
            TopicManager.add_custom_topic(test_topic)
            assert "removable_topic" in TopicManager.TOPICS

            # Remove the topic
            result = TopicManager.remove_topic("removable_topic")
            assert result is True
            assert "removable_topic" not in TopicManager.TOPICS

        finally:
            TopicManager.TOPICS = original_topics

    def test_remove_topic_not_found(self):
        """Test removing a non-existent topic."""
        result = TopicManager.remove_topic("nonexistent_topic")
        assert result is False


class TestSubjectValidation:
    """Test subject validation functionality."""

    def test_validate_subject_valid_discovery(self):
        """Test validating a valid discovery subject."""
        subject = "tenant.discovery.session-123.progress"
        assert TopicManager.validate_subject(subject) is True

    def test_validate_subject_valid_system(self):
        """Test validating a valid system subject."""
        subject = "system.graph_db.health"
        assert TopicManager.validate_subject(subject) is True

    def test_validate_subject_valid_simulation(self):
        """Test validating a valid simulation subject."""
        subject = "simulation.sim-456.status"
        assert TopicManager.validate_subject(subject) is True

    def test_validate_subject_invalid(self):
        """Test validating an invalid subject."""
        subject = "invalid.unknown.pattern"
        assert TopicManager.validate_subject(subject) is False

    def test_get_topic_for_subject_discovery(self):
        """Test finding topic for discovery subject."""
        subject = "tenant.discovery.session-123.progress"
        topic = TopicManager.get_topic_for_subject(subject)

        assert topic is not None
        assert topic.name == "tenant_discovery"

    def test_get_topic_for_subject_system(self):
        """Test finding topic for system subject."""
        subject = "system.component.event"
        topic = TopicManager.get_topic_for_subject(subject)

        assert topic is not None
        assert topic.name == "system_events"

    def test_get_topic_for_subject_simulation(self):
        """Test finding topic for simulation subject."""
        subject = "simulation.sim-123.progress"
        topic = TopicManager.get_topic_for_subject(subject)

        assert topic is not None
        assert topic.name == "simulation_events"

    def test_get_topic_for_subject_no_match(self):
        """Test finding topic for unmatched subject."""
        subject = "unknown.pattern.here"
        topic = TopicManager.get_topic_for_subject(subject)

        assert topic is None


class TestConvenienceFunctions:
    """Test convenience functions for subject generation."""

    def test_discovery_subject_function(self):
        """Test discovery_subject convenience function."""
        session_id = "test-session"
        event_type = "start"

        subject = discovery_subject(session_id, event_type)
        assert subject == "tenant.discovery.test-session.start"

        # Should match the class method
        expected = TopicManager.get_subject_for_discovery(session_id, event_type)
        assert subject == expected

    def test_simulation_subject_function(self):
        """Test simulation_subject convenience function."""
        simulation_id = "test-sim"
        event_type = "complete"

        subject = simulation_subject(simulation_id, event_type)
        assert subject == "simulation.test-sim.complete"

        # Should match the class method
        expected = TopicManager.get_subject_for_simulation(simulation_id, event_type)
        assert subject == expected

    def test_system_subject_function(self):
        """Test system_subject convenience function."""
        component = "api"
        event_type = "startup"

        subject = system_subject(component, event_type)
        assert subject == "system.api.startup"

        # Should match the class method
        expected = TopicManager.get_subject_for_system(component, event_type)
        assert subject == expected


class TestTopicIntegrity:
    """Test topic definition integrity and consistency."""

    def test_all_topics_have_required_fields(self):
        """Test that all predefined topics have required fields."""
        for topic in TopicManager.get_all_topics():
            assert topic.name
            assert topic.subject_pattern
            assert topic.description
            assert topic.message_types
            assert len(topic.message_types) > 0
            assert topic.max_age_seconds > 0
            assert topic.max_messages > 0
            assert topic.replicas >= 1

    def test_topic_subject_patterns_unique(self):
        """Test that topic subject patterns don't overlap inappropriately."""
        topics = TopicManager.get_all_topics()
        patterns = [topic.subject_pattern for topic in topics]

        # Check that we don't have exact duplicates
        assert len(patterns) == len(set(patterns))

        # Check specific patterns that shouldn't conflict
        discovery_topics = [t for t in topics if "discovery" in t.name.lower()]
        system_topics = [t for t in topics if "system" in t.name.lower()]
        simulation_topics = [t for t in topics if "simulation" in t.name.lower()]

        # Each category should have distinct patterns
        assert len(discovery_topics) >= 1
        assert len(system_topics) >= 1
        assert len(simulation_topics) >= 1

    def test_message_types_consistency(self):
        """Test that message types are consistently used across topics."""
        for topic in TopicManager.get_all_topics():
            # All message types should be valid enum values
            for msg_type in topic.message_types:
                assert isinstance(msg_type, MessageType)

            # Topic-specific checks
            if "discovery" in topic.name.lower():
                # Discovery topics should support progress updates
                assert MessageType.PROGRESS_UPDATE in topic.message_types

            if "system" in topic.name.lower():
                # System topics should support status messages
                assert MessageType.SYSTEM_STATUS in topic.message_types
