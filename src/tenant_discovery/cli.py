"""Tenant Discovery CLI interface."""

import sys

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from src.simbuilder_graph.cli import app as graph_app

from .config import get_td_settings

app = typer.Typer(
    name="tdcli",
    help="Tenant Discovery CLI",
    no_args_is_help=True,
)

# Create subcommands
config_app = typer.Typer(name="config", help="Configuration management commands")
discovery_app = typer.Typer(name="discovery", help="Tenant discovery management commands")

app.add_typer(config_app, name="config")
app.add_typer(discovery_app, name="discovery")
app.add_typer(graph_app, name="graph")

console = Console()


@config_app.command()
def info() -> None:
    """Display current configuration settings."""
    try:
        settings = get_td_settings()

        # Create a table to display settings
        table = Table(title="Tenant Discovery Configuration", show_header=True)
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_column("Description", style="green")

        # Mask sensitive values
        masked_secret = (
            "***" + settings.azure_client_secret[-4:]
            if len(settings.azure_client_secret) > 4
            else "***"
        )

        table.add_row(
            "Azure Tenant ID", settings.azure_tenant_id, "Azure tenant ID for authentication"
        )
        table.add_row(
            "Azure Client ID", settings.azure_client_id, "Azure client ID for authentication"
        )
        table.add_row("Azure Client Secret", masked_secret, "Azure client secret (masked)")
        table.add_row(
            "Subscription ID",
            settings.subscription_id,
            "Azure subscription ID for resource discovery",
        )
        table.add_row("Graph DB URL", settings.graph_db_url, "Neo4j graph database connection URL")
        table.add_row(
            "Service Bus URL", settings.service_bus_url, "NATS service bus connection URL"
        )
        table.add_row("Log Level", settings.log_level.value, "Logging level for the service")

        console.print(table)
        console.print("\n[green]✓[/green] Configuration loaded successfully")

    except ValidationError as e:
        console.print("[red]✗[/red] Configuration validation failed:")
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            console.print(f"  • {field}: {error['msg']}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]✗[/red] Error loading configuration: {e}")
        raise typer.Exit(1) from e


@config_app.command()
def check() -> None:
    """Validate configuration and environment variables."""
    try:
        settings = get_td_settings()

        console.print("[bold]Validating Tenant Discovery configuration...[/bold]\n")

        checks = [
            ("Azure Tenant ID format", settings.azure_tenant_id),
            ("Azure Client ID format", settings.azure_client_id),
            ("Azure Client Secret presence", bool(settings.azure_client_secret)),
            ("Subscription ID format", settings.subscription_id),
            ("Graph DB URL format", settings.graph_db_url),
            ("Service Bus URL format", settings.service_bus_url),
            ("Log Level validity", settings.log_level.value),
        ]

        all_passed = True
        for check_name, check_value in checks:
            if check_value:
                console.print(f"[green]✓[/green] {check_name}")
            else:
                console.print(f"[red]✗[/red] {check_name}")
                all_passed = False

        if all_passed:
            console.print("\n[green]✓[/green] All configuration checks passed!")
            sys.exit(0)
        else:
            console.print("\n[red]✗[/red] Some configuration checks failed!")
            sys.exit(1)

    except ValidationError as e:
        console.print("[red]✗[/red] Configuration validation failed:")
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            console.print(f"  • {field}: {error['msg']}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error validating configuration: {e}")
        sys.exit(1)


# Discovery commands
@discovery_app.command()
@discovery_app.command("run")  # Alias for start
def start(
    tenant_id: str = typer.Option(
        None, "--tenant-id", help="Azure tenant ID for discovery (overrides config)"
    ),
) -> None:
    """Start tenant resource discovery."""
    try:
        settings = get_td_settings()
        # Use provided tenant_id or fall back to settings
        effective_tenant_id = tenant_id or settings.azure_tenant_id

        console.print(f"[green]Discovery started for {effective_tenant_id}[/green]")
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] Error starting discovery: {e}")
        sys.exit(1)


@discovery_app.command()
def list() -> None:
    """List discovery sessions."""
    try:
        # Fake data for now - will be replaced with real implementation later
        table = Table(title="Discovery Sessions", show_header=True)
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Tenant ID", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Started", style="blue")

        # Sample fake data
        table.add_row(
            "session-001", "12345678-1234-1234-1234-123456789012", "Running", "2025-06-10 23:45:00"
        )
        table.add_row(
            "session-002",
            "87654321-4321-4321-4321-210987654321",
            "Completed",
            "2025-06-10 23:30:00",
        )

        console.print(table)
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] Error listing discovery sessions: {e}")
        sys.exit(1)


@discovery_app.command()
def status(
    session_id: str = typer.Argument(None, help="Session ID to check status for (optional)")
) -> None:
    """Show status of a discovery session."""
    try:
        if session_id:
            console.print(f"[cyan]Status for session {session_id}:[/cyan]")
            console.print("[green]Status: Running[/green]")
            console.print("[blue]Progress: 45% (23 of 51 resources discovered)[/blue]")
            console.print("[yellow]Started: 2025-06-10 23:45:00[/yellow]")
        else:
            console.print(
                "[yellow]No session ID provided. Use 'tdcli discovery list' to see available sessions.[/yellow]"
            )

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] Error getting discovery status: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
