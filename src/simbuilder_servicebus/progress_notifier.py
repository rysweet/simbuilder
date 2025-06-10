"""Progress notification system for long-running operations."""

import uuid
from datetime import datetime
from datetime import timedelta

from src.scaffolding.logging import LoggingMixin

from .client import ServiceBusClient
from .models import ProgressMessage
from .topics import discovery_subject


class ProgressNotifier(LoggingMixin):
    """High-level interface for sending progress notifications."""

    def __init__(self,
                 session_id: str,
                 operation: str,
                 client: ServiceBusClient | None = None):
        """Initialize progress notifier.

        Args:
            session_id: Session identifier for the operation
            operation: Name of the operation being tracked
            client: Optional ServiceBus client (creates new one if None)
        """
        super().__init__()
        self.session_id = session_id
        self.operation = operation
        self._client = client
        self._own_client = client is None

        # Progress tracking
        self._total_steps: int | None = None
        self._current_step = 0
        self._start_time = datetime.utcnow()
        self._last_update_time = self._start_time

    async def __aenter__(self):
        """Async context manager entry."""
        if self._own_client:
            self._client = ServiceBusClient()
            await self._client.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_client and self._client:
            await self._client.disconnect()

    async def start_operation(self, total_steps: int | None = None) -> None:
        """Signal the start of an operation.

        Args:
            total_steps: Total number of steps in the operation
        """
        self._total_steps = total_steps
        self._current_step = 0
        self._start_time = datetime.utcnow()
        self._last_update_time = self._start_time

        await self._send_progress_message(
            progress_percentage=0.0,
            current_step="Starting operation",
            details=f"Beginning {self.operation}"
        )

        self.logger.info(
            "Operation started",
            session_id=self.session_id,
            operation=self.operation,
            total_steps=total_steps
        )

    async def update_progress(self,
                            progress_percentage: float | None = None,
                            current_step: str | None = None,
                            step_number: int | None = None,
                            details: str | None = None) -> None:
        """Update operation progress.

        Args:
            progress_percentage: Completion percentage (0-100)
            current_step: Description of current step
            step_number: Current step number
            details: Additional details about progress
        """
        if step_number is not None:
            self._current_step = step_number

        # Calculate progress percentage if not provided
        if progress_percentage is None and self._total_steps:
            progress_percentage = (self._current_step / self._total_steps) * 100

        # Estimate completion time
        estimated_completion = None
        if progress_percentage and progress_percentage > 0:
            elapsed = datetime.utcnow() - self._start_time
            total_estimated = elapsed * (100 / progress_percentage)
            estimated_completion = self._start_time + total_estimated

        await self._send_progress_message(
            progress_percentage=progress_percentage or 0.0,
            current_step=current_step or f"Step {self._current_step}",
            step_number=step_number,
            estimated_completion=estimated_completion,
            details=details
        )

        self._last_update_time = datetime.utcnow()

        self.logger.debug(
            "Progress updated",
            session_id=self.session_id,
            operation=self.operation,
            progress_percentage=progress_percentage,
            current_step=current_step
        )

    async def advance_step(self,
                          step_description: str,
                          details: str | None = None) -> None:
        """Advance to the next step and update progress.

        Args:
            step_description: Description of the new current step
            details: Additional details about the step
        """
        self._current_step += 1

        progress_percentage = None
        if self._total_steps:
            progress_percentage = (self._current_step / self._total_steps) * 100

        await self.update_progress(
            progress_percentage=progress_percentage,
            current_step=step_description,
            step_number=self._current_step,
            details=details
        )

    async def complete_operation(self, details: str | None = None) -> None:
        """Signal the completion of an operation.

        Args:
            details: Additional completion details
        """
        completion_time = datetime.utcnow()
        duration = completion_time - self._start_time

        # Format completion details with timing
        completion_details = f"Completed in {duration.total_seconds():.1f} seconds"
        if details:
            completion_details = f"{details}. {completion_details}"

        await self._send_progress_message(
            progress_percentage=100.0,
            current_step="Operation completed",
            step_number=self._total_steps,
            details=completion_details
        )

        self.logger.info(
            "Operation completed",
            session_id=self.session_id,
            operation=self.operation,
            duration_seconds=duration.total_seconds(),
            total_steps=self._current_step
        )

    async def error_occurred(self,
                           error: Exception,
                           current_step: str | None = None,
                           details: str | None = None) -> None:
        """Signal that an error occurred during the operation.

        Args:
            error: The error that occurred
            current_step: Step where error occurred
            details: Additional error details
        """
        error_details = details or f"Error: {str(error)}"

        await self._send_progress_message(
            progress_percentage=None,  # Don't update percentage on error
            current_step=current_step or f"Error in step {self._current_step}",
            step_number=self._current_step,
            details=error_details
        )

        self.log_error(error, {
            "session_id": self.session_id,
            "operation": self.operation,
            "current_step": self._current_step
        })

    async def _send_progress_message(self,
                                   progress_percentage: float | None,
                                   current_step: str,
                                   step_number: int | None = None,
                                   estimated_completion: datetime | None = None,
                                   details: str | None = None) -> None:
        """Send a progress message via Service Bus.

        Args:
            progress_percentage: Completion percentage (None for errors)
            current_step: Current step description
            step_number: Current step number
            estimated_completion: Estimated completion time
            details: Additional details
        """
        if not self._client:
            self.logger.warning("No Service Bus client available for progress notification")
            return

        try:
            message = ProgressMessage(
                message_id=str(uuid.uuid4()),
                session_id=self.session_id,
                source=f"{self.operation}_notifier",
                operation=self.operation,
                progress_percentage=progress_percentage,
                current_step=current_step,
                total_steps=self._total_steps,
                current_step_number=step_number,
                estimated_completion=estimated_completion,
                details=details
            )

            subject = discovery_subject(self.session_id, "progress")
            await self._client.publish(subject, message)

        except Exception as e:
            self.log_error(e, {
                "operation": "send_progress_message",
                "session_id": self.session_id
            })
            # Don't re-raise - progress notifications shouldn't break the main operation

    def get_elapsed_time(self) -> timedelta:
        """Get elapsed time since operation start.

        Returns:
            Time elapsed since operation started
        """
        return datetime.utcnow() - self._start_time

    def get_time_since_last_update(self) -> timedelta:
        """Get time since last progress update.

        Returns:
            Time since last progress update
        """
        return datetime.utcnow() - self._last_update_time

    @property
    def current_step_number(self) -> int:
        """Get current step number."""
        return self._current_step

    @property
    def total_steps(self) -> int | None:
        """Get total number of steps."""
        return self._total_steps

    @property
    def estimated_progress_percentage(self) -> float | None:
        """Get estimated progress percentage based on steps."""
        if not self._total_steps or self._total_steps == 0:
            return None
        return (self._current_step / self._total_steps) * 100


# Convenience function for simple progress tracking
async def track_progress(session_id: str,
                        operation: str,
                        total_steps: int | None = None) -> ProgressNotifier:
    """Create and initialize a progress notifier.

    Args:
        session_id: Session identifier
        operation: Operation name
        total_steps: Total number of steps

    Returns:
        Initialized progress notifier
    """
    notifier = ProgressNotifier(session_id, operation)
    await notifier.__aenter__()
    await notifier.start_operation(total_steps)
    return notifier
