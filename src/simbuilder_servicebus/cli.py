"""CLI interface for Service Bus management."""

import asyncio
import json

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .client import ServiceBusClient
from .models import MessagePriority
from .models import MessageSchema
from .models import MessageType
from .progress_notifier import ProgressNotifier
from .topics import TopicManager

app = typer.Typer(name="servicebus", help="Service Bus management commands")
console = Console()


@app.command()
def info() -> None:
    """Display Service Bus configuration and status."""
    try:
        async def _info() -> None:
            async with ServiceBusClient() as client:
                health = await client.health_check()

                # Create status table
                table = Table(title="Service Bus Status", show_header=True)
                table.add_column("Property", style="cyan", no_wrap=True)
                table.add_column("Value", style="magenta")

                table.add_row("Connected", "✅ Yes" if health["connected"] else "❌ No")
                table.add_row("Client ID", health["client_id"])
                table.add_row("Servers", ", ".join(health["servers"]))

                if health["connected"]:
                    table.add_row("RTT", f"{health.get('rtt_ms', 'N/A')} ms")
                    table.add_row("Server Version", health.get("server_info", "N/A"))
                    table.add_row("Active Subscriptions", str(health.get("active_subscriptions", 0)))
                    table.add_row("Active Streams", str(health.get("active_streams", 0)))

                console.print(table)

                # Show topics
                topics_table = Table(title="Available Topics", show_header=True)
                topics_table.add_column("Name", style="cyan")
                topics_table.add_column("Subject Pattern", style="green")
                topics_table.add_column("Message Types", style="yellow")
                topics_table.add_column("Retention", style="blue")

                for topic in TopicManager.get_all_topics():
                    message_types = ", ".join([mt.value for mt in topic.message_types])
                    topics_table.add_row(
                        topic.name,
                        topic.subject_pattern,
                        message_types,
                        f"{topic.retention_policy} ({topic.max_age_seconds}s)"
                    )

                console.print(topics_table)

        asyncio.run(_info())

    except Exception as e:
        console.print(f"[red]✗[/red] Error getting Service Bus info: {e}")
        raise typer.Exit(1) from e


@app.command()
def health() -> None:
    """Perform health check on Service Bus connection."""
    try:
        async def _health() -> None:
            async with ServiceBusClient() as client:
                health = await client.health_check()

                if health["connected"]:
                    console.print("[green]✅ Service Bus is healthy[/green]")
                    console.print(f"Round-trip time: {health.get('rtt_ms', 'N/A')} ms")
                else:
                    console.print("[red]❌ Service Bus is not connected[/red]")
                    if "error" in health:
                        console.print(f"Error: {health['error']}")
                    raise typer.Exit(1)

        asyncio.run(_health())

    except Exception as e:
        console.print(f"[red]✗[/red] Health check failed: {e}")
        raise typer.Exit(1) from e


@app.command()
def setup_topics() -> None:
    """Create all predefined topics and streams."""
    try:
        async def _setup() -> None:
            async with ServiceBusClient() as client:
                topics = TopicManager.get_all_topics()

                console.print(f"Setting up {len(topics)} topics...")

                for topic in topics:
                    try:
                        stream_info = await client.create_stream(topic)
                        console.print(f"✅ Created/updated topic: {topic.name}")
                        console.print(f"   Stream: {stream_info.config.name}")
                        console.print(f"   Messages: {stream_info.state.messages}")
                    except Exception as e:
                        console.print(f"❌ Failed to create topic {topic.name}: {e}")

                console.print("[green]Topic setup completed[/green]")

        asyncio.run(_setup())

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to setup topics: {e}")
        raise typer.Exit(1) from e


@app.command()
def publish(
    subject: str = typer.Argument(..., help="NATS subject to publish to"),
    message_type: str = typer.Option("system_status", help="Message type"),
    session_id: str | None = typer.Option(None, help="Session ID"),
    data: str = typer.Option("{}", help="Message data as JSON string"),
) -> None:
    """Publish a test message to a subject."""
    try:
        async def _publish() -> None:
            # Parse message data
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON data: {e}[/red]")
                raise typer.Exit(1) from e

            # Create message
            message = MessageSchema(
                message_id=f"cli-{asyncio.get_event_loop().time()}",
                message_type=MessageType(message_type),
                session_id=session_id,
                source="cli",
                data=message_data,
                priority=MessagePriority.NORMAL
            )

            async with ServiceBusClient() as client:
                message_id = await client.publish(subject, message)
                console.print(f"[green]✅ Published message {message_id} to {subject}[/green]")

        asyncio.run(_publish())

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to publish message: {e}")
        raise typer.Exit(1) from e


@app.command()
def subscribe(
    subject_pattern: str = typer.Argument(..., help="Subject pattern to subscribe to"),
    duration: int = typer.Option(30, help="How long to listen in seconds"),
) -> None:
    """Subscribe to messages and display them."""
    try:
        async def _subscribe() -> None:
            messages_received = 0

            async def message_handler(message: MessageSchema) -> None:
                nonlocal messages_received
                messages_received += 1

                panel = Panel(
                    f"[bold]Message #{messages_received}[/bold]\n"
                    f"ID: {message.message_id}\n"
                    f"Type: {message.message_type}\n"
                    f"Source: {message.source}\n"
                    f"Session: {message.session_id or 'None'}\n"
                    f"Time: {message.timestamp}\n"
                    f"Data: {json.dumps(message.data, indent=2)}",
                    title=f"Subject: {subject_pattern}",
                    border_style="green"
                )
                console.print(panel)

            from .models import SubscriptionConfig
            config = SubscriptionConfig(
                name=f"cli-subscriber-{asyncio.get_event_loop().time()}",
                topic="test",  # Will be overridden by subject_filter
                subject_filter=subject_pattern,
                queue_group=None,
                durable=False,
                auto_ack=True,
                max_pending=1000,
                ack_wait_seconds=30
            )

            async with ServiceBusClient() as client:
                console.print(f"[yellow]Listening for messages on '{subject_pattern}' for {duration} seconds...[/yellow]")
                console.print("[dim]Press Ctrl+C to stop early[/dim]")

                subscription_id = await client.subscribe(config, message_handler)

                try:
                    await asyncio.sleep(duration)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping subscription...[/yellow]")

                await client.unsubscribe(subscription_id)
                console.print(f"[green]Received {messages_received} messages[/green]")

        asyncio.run(_subscribe())

    except Exception as e:
        console.print(f"[red]✗[/red] Subscription failed: {e}")
        raise typer.Exit(1) from e


@app.command()
def demo_progress(
    session_id: str = typer.Argument(..., help="Session ID for progress tracking"),
    steps: int = typer.Option(10, help="Number of steps to simulate"),
    delay: float = typer.Option(1.0, help="Delay between steps in seconds"),
) -> None:
    """Demonstrate progress notifications."""
    try:
        async def _demo() -> None:
            async with ProgressNotifier(session_id, "demo_operation") as notifier:
                await notifier.start_operation(total_steps=steps)

                with Live(console=console, refresh_per_second=2) as live:
                    for i in range(steps):
                        step_desc = f"Processing step {i + 1} of {steps}"
                        await notifier.advance_step(
                            step_desc,
                            details=f"Demo step with {delay}s delay"
                        )

                        # Update live display
                        progress = notifier.estimated_progress_percentage or 0
                        elapsed = notifier.get_elapsed_time()

                        progress_panel = Panel(
                            f"[bold]Progress Demo[/bold]\n"
                            f"Session: {session_id}\n"
                            f"Step: {i + 1}/{steps}\n"
                            f"Progress: {progress:.1f}%\n"
                            f"Elapsed: {elapsed.total_seconds():.1f}s\n"
                            f"Current: {step_desc}",
                            title="Progress Notification Demo",
                            border_style="blue"
                        )
                        live.update(progress_panel)

                        await asyncio.sleep(delay)

                await notifier.complete_operation("Demo completed successfully")
                console.print("[green]✅ Progress demo completed[/green]")

        asyncio.run(_demo())

    except Exception as e:
        console.print(f"[red]✗[/red] Progress demo failed: {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
