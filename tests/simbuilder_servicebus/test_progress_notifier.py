"""Tests for Service Bus progress notification system."""

import asyncio
from datetime import datetime
from datetime import timedelta
from unittest.mock import AsyncMock
from unittest.mock import patch
from uuid import uuid4

import pytest

from src.simbuilder_servicebus.client import ServiceBusClient
from src.simbuilder_servicebus.models import MessageType
from src.simbuilder_servicebus.models import ProgressMessage
from src.simbuilder_servicebus.progress_notifier import ProgressNotifier
from src.simbuilder_servicebus.progress_notifier import track_progress


@pytest.fixture
def mock_client():
    """Create a mock ServiceBusClient."""
    client = AsyncMock(spec=ServiceBusClient)
    client.publish = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    return client


class TestProgressNotifier:
    """Test ProgressNotifier functionality."""

    @pytest.fixture
    def notifier(self, mock_client):
        """Create a ProgressNotifier with mock client."""
        session_id = str(uuid4())
        return ProgressNotifier(session_id, "test_operation", client=mock_client)

    def test_notifier_initialization(self):
        """Test ProgressNotifier initialization."""
        session_id = "test-session-123"
        operation = "test_operation"

        notifier = ProgressNotifier(session_id, operation)

        assert notifier.session_id == session_id
        assert notifier.operation == operation
        assert notifier._client is None  # No client provided
        assert notifier._own_client is True  # Should create own client
        assert notifier._total_steps is None
        assert notifier._current_step == 0

    def test_notifier_with_provided_client(self, mock_client):
        """Test ProgressNotifier with provided client."""
        session_id = "test-session-456"
        operation = "test_operation"

        notifier = ProgressNotifier(session_id, operation, client=mock_client)

        assert notifier._client is mock_client
        assert notifier._own_client is False  # Using provided client

    @pytest.mark.asyncio
    async def test_context_manager_with_own_client(self):
        """Test ProgressNotifier as async context manager with own client."""
        session_id = "test-session-789"
        operation = "test_operation"

        with patch(
            "src.simbuilder_servicebus.progress_notifier.ServiceBusClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            async with ProgressNotifier(session_id, operation) as notifier:
                assert notifier._client is mock_client
                mock_client.connect.assert_called_once()

            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_provided_client(self, mock_client):
        """Test ProgressNotifier as async context manager with provided client."""
        session_id = "test-session-101"
        operation = "test_operation"

        async with ProgressNotifier(session_id, operation, client=mock_client) as notifier:
            assert notifier._client is mock_client
            # Should not call connect/disconnect on provided client
            mock_client.connect.assert_not_called()

        mock_client.disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_operation(self, notifier, mock_client):
        """Test starting an operation."""
        total_steps = 5

        await notifier.start_operation(total_steps)

        assert notifier._total_steps == total_steps
        assert notifier._current_step == 0
        assert isinstance(notifier._start_time, datetime)

        # Verify message was published
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        subject, message = call_args[0]

        assert subject == f"tenant.discovery.{notifier.session_id}.progress"
        assert isinstance(message, ProgressMessage)
        assert message.message_type == MessageType.PROGRESS_UPDATE
        assert message.operation == "test_operation"
        assert message.progress_percentage == 0.0
        assert message.current_step == "Starting operation"
        assert message.total_steps == total_steps

    @pytest.mark.asyncio
    async def test_update_progress(self, notifier, mock_client):
        """Test updating progress."""
        await notifier.start_operation(10)
        mock_client.publish.reset_mock()  # Reset after start_operation call

        await notifier.update_progress(
            progress_percentage=50.0,
            current_step="Processing data",
            step_number=5,
            details="Halfway through processing",
        )

        assert notifier._current_step == 5

        # Verify message was published
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        subject, message = call_args[0]

        assert isinstance(message, ProgressMessage)
        assert message.progress_percentage == 50.0
        assert message.current_step == "Processing data"
        assert message.current_step_number == 5
        assert message.details == "Halfway through processing"
        assert message.estimated_completion is not None

    @pytest.mark.asyncio
    async def test_update_progress_auto_calculate(self, notifier, mock_client):
        """Test updating progress with automatic percentage calculation."""
        await notifier.start_operation(10)
        mock_client.publish.reset_mock()

        notifier._current_step = 3
        await notifier.update_progress(current_step="Step 3 of 10")

        # Verify percentage was calculated automatically
        call_args = mock_client.publish.call_args
        subject, message = call_args[0]

        assert message.progress_percentage == 30.0  # 3/10 * 100

    @pytest.mark.asyncio
    async def test_advance_step(self, notifier, mock_client):
        """Test advancing to next step."""
        await notifier.start_operation(5)
        mock_client.publish.reset_mock()

        await notifier.advance_step("Processing step 1", "First step details")

        assert notifier._current_step == 1

        # Verify message was published
        call_args = mock_client.publish.call_args
        subject, message = call_args[0]

        assert message.current_step == "Processing step 1"
        assert message.current_step_number == 1
        assert message.details == "First step details"
        assert message.progress_percentage == 20.0  # 1/5 * 100

    @pytest.mark.asyncio
    async def test_complete_operation(self, notifier, mock_client):
        """Test completing an operation."""
        await notifier.start_operation(3)

        # Simulate some time passing
        notifier._start_time = datetime.utcnow() - timedelta(seconds=5)
        mock_client.publish.reset_mock()

        await notifier.complete_operation("All tasks completed successfully")

        # Verify completion message
        call_args = mock_client.publish.call_args
        subject, message = call_args[0]

        assert message.progress_percentage == 100.0
        assert message.current_step == "Operation completed"
        assert message.current_step_number == 3  # total_steps
        assert "Completed in" in message.details
        assert "5." in message.details  # Should show ~5 seconds

    @pytest.mark.asyncio
    async def test_error_occurred(self, notifier, mock_client):
        """Test handling an error during operation."""
        await notifier.start_operation(5)
        notifier._current_step = 2
        mock_client.publish.reset_mock()

        test_error = ValueError("Something went wrong")
        await notifier.error_occurred(test_error, "Step 2", "Additional error context")

        # Verify error message
        call_args = mock_client.publish.call_args
        subject, message = call_args[0]

        assert message.current_step == "Step 2"
        assert message.current_step_number == 2
        assert message.details == "Additional error context"
        # Progress percentage should not be updated on error
        assert message.progress_percentage is None

    @pytest.mark.asyncio
    async def test_error_occurred_default_step(self, notifier, mock_client):
        """Test error handling with default step description."""
        await notifier.start_operation(5)
        notifier._current_step = 3
        mock_client.publish.reset_mock()

        test_error = RuntimeError("Test error")
        await notifier.error_occurred(test_error)

        call_args = mock_client.publish.call_args
        subject, message = call_args[0]

        assert message.current_step == "Error in step 3"
        assert "Error: Test error" in message.details

    @pytest.mark.asyncio
    async def test_publish_error_handling(self, notifier, mock_client):
        """Test handling publish errors gracefully."""
        mock_client.publish.side_effect = Exception("NATS connection failed")

        # Should not raise exception
        await notifier.start_operation(5)

        # Verify it tried to publish
        mock_client.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_client_available(self):
        """Test behavior when no client is available."""
        notifier = ProgressNotifier("test-session", "test_operation")
        # Don't set up client

        # Should not raise exception
        await notifier._send_progress_message(50.0, "Test step")

    def test_elapsed_time_calculation(self, notifier):
        """Test elapsed time calculation."""
        start_time = datetime.utcnow() - timedelta(seconds=10)
        notifier._start_time = start_time

        elapsed = notifier.get_elapsed_time()

        assert isinstance(elapsed, timedelta)
        assert elapsed.total_seconds() >= 9  # Allow some margin for test execution

    def test_time_since_last_update(self, notifier):
        """Test time since last update calculation."""
        last_update = datetime.utcnow() - timedelta(seconds=5)
        notifier._last_update_time = last_update

        time_since = notifier.get_time_since_last_update()

        assert isinstance(time_since, timedelta)
        assert time_since.total_seconds() >= 4  # Allow some margin

    def test_property_accessors(self, notifier):
        """Test property accessors."""
        notifier._current_step = 3
        notifier._total_steps = 10

        assert notifier.current_step_number == 3
        assert notifier.total_steps == 10
        assert notifier.estimated_progress_percentage == 30.0

    def test_estimated_progress_no_total_steps(self, notifier):
        """Test estimated progress when total steps is not set."""
        notifier._current_step = 5
        notifier._total_steps = None

        assert notifier.estimated_progress_percentage is None

    def test_estimated_progress_zero_total_steps(self, notifier):
        """Test estimated progress when total steps is zero."""
        notifier._current_step = 5
        notifier._total_steps = 0

        assert notifier.estimated_progress_percentage is None


class TestTrackProgressConvenienceFunction:
    """Test the track_progress convenience function."""

    @pytest.mark.asyncio
    async def test_track_progress_function(self):
        """Test track_progress convenience function."""
        session_id = "convenience-test"
        operation = "test_operation"
        total_steps = 5

        with patch(
            "src.simbuilder_servicebus.progress_notifier.ProgressNotifier"
        ) as mock_notifier_class:
            mock_notifier = AsyncMock()
            mock_notifier_class.return_value = mock_notifier

            result = await track_progress(session_id, operation, total_steps)

            # Verify notifier was created and configured correctly
            mock_notifier_class.assert_called_once_with(session_id, operation)
            mock_notifier.__aenter__.assert_called_once()
            mock_notifier.start_operation.assert_called_once_with(total_steps)

            assert result is mock_notifier


class TestProgressNotifierIntegration:
    """Integration tests for ProgressNotifier with real-like scenarios."""

    @pytest.mark.asyncio
    async def test_full_operation_lifecycle(self, mock_client):
        """Test a complete operation lifecycle."""
        session_id = "integration-test"
        operation = "full_operation"

        notifier = ProgressNotifier(session_id, operation, client=mock_client)

        # Start operation
        await notifier.start_operation(total_steps=3)

        # Advance through steps
        await notifier.advance_step("Step 1: Initialize")
        await notifier.advance_step("Step 2: Process")
        await notifier.advance_step("Step 3: Finalize")

        # Complete operation
        await notifier.complete_operation("Successfully completed all steps")

        # Verify all messages were published
        assert (
            mock_client.publish.call_count == 5
        )  # start + 3 steps + complete (complete does its own publish after progress)

        # Check final state
        assert notifier.current_step_number == 3
        assert notifier.total_steps == 3
        assert notifier.estimated_progress_percentage == 100.0

    @pytest.mark.asyncio
    async def test_operation_with_error_recovery(self, mock_client):
        """Test operation that encounters an error but continues."""
        session_id = "error-recovery-test"
        operation = "error_recovery_operation"

        notifier = ProgressNotifier(session_id, operation, client=mock_client)

        # Start operation
        await notifier.start_operation(total_steps=4)

        # Progress through some steps
        await notifier.advance_step("Step 1: OK")
        await notifier.advance_step("Step 2: OK")

        # Encounter an error
        error = ConnectionError("Network temporarily unavailable")
        await notifier.error_occurred(error, "Step 3: Network operation")

        # Continue after error handling
        await notifier.advance_step("Step 3: Retry successful")
        await notifier.advance_step("Step 4: Cleanup")

        # Complete operation
        await notifier.complete_operation("Completed with error recovery")

        # Verify all messages were published
        assert (
            mock_client.publish.call_count == 7
        )  # start + 2 steps + error + 2 steps + complete (complete triggers extra publish)

    @pytest.mark.asyncio
    async def test_concurrent_notifiers(self, mock_client):
        """Test multiple notifiers running concurrently."""
        session_ids = ["concurrent-1", "concurrent-2", "concurrent-3"]
        notifiers = [
            ProgressNotifier(session_id, f"operation_{i}", client=mock_client)
            for i, session_id in enumerate(session_ids)
        ]

        # Start all operations concurrently
        await asyncio.gather(*[notifier.start_operation(total_steps=2) for notifier in notifiers])

        # Update progress concurrently
        await asyncio.gather(
            *[notifier.advance_step(f"Step 1 for {notifier.session_id}") for notifier in notifiers]
        )

        await asyncio.gather(
            *[
                notifier.complete_operation(f"Completed {notifier.session_id}")
                for notifier in notifiers
            ]
        )

        # Verify all messages were published (3 notifiers * 3 messages each)
        assert mock_client.publish.call_count == 9

        # Verify each notifier maintained its own state
        for notifier in notifiers:
            assert notifier.current_step_number == 1
            assert notifier.total_steps == 2
