"""Tenant Discovery CLI interface."""

import sys

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from src.scaffolding.exceptions import ConfigurationError
from .config import get_td_settings
from .graph import get_graph_service

app = typer.Typer(
    name="tdcli",
    help="Tenant Discovery CLI",
    no_args_is_help=True,
)

# Create subcommands
config_app = typer.Typer(name="config", help="Configuration management commands")
graph_app = typer.Typer(name="graph", help="Graph database commands")

app.add_typer(config_app, name="config")
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
        masked_secret = "***" + settings.azure_client_secret[-4:] if len(settings.azure_client_secret) > 4 else "***"

        table.add_row("Azure Tenant ID", settings.azure_tenant_id, "Azure tenant ID for authentication")
        table.add_row("Azure Client ID", settings.azure_client_id, "Azure client ID for authentication")
        table.add_row("Azure Client Secret", masked_secret, "Azure client secret (masked)")
        table.add_row("Subscription ID", settings.subscription_id, "Azure subscription ID for resource discovery")
        table.add_row("Graph DB URL", settings.graph_db_url, "Neo4j graph database connection URL")
        table.add_row("Service Bus URL", settings.service_bus_url, "NATS service bus connection URL")
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


@graph_app.command("info")
def graph_info() -> None:
    """Display graph database information and statistics."""
    try:
        service = get_graph_service()

        console.print("[bold]Connecting to graph database...[/bold]")

        with service:
            # Check connectivity
            if not service.check_connectivity():
                console.print("[red]✗[/red] Failed to connect to graph database")
                raise typer.Exit(1)

            # Get node counts
            counts = service.get_node_counts()

            # Create information table
            table = Table(title="Graph Database Information", show_header=True)
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")
            table.add_column("Description", style="green")

            table.add_row("Connection Status", "✓ Connected", "Database connectivity")
            table.add_row("Tenants", str(counts["tenants"]), "Number of tenant nodes")
            table.add_row("Subscriptions", str(counts["subscriptions"]), "Number of subscription nodes")

            console.print(table)
            console.print("\n[green]✓[/green] Graph database information retrieved successfully")

    except ConfigurationError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]✗[/red] Error connecting to graph database: {e}")
        raise typer.Exit(1) from e


@graph_app.command("check")
def graph_check() -> None:
    """Check graph database connectivity and health."""
    try:
        service = get_graph_service()

        console.print("[bold]Checking graph database connectivity...[/bold]\n")

        checks = []

        # Test connection
        try:
            with service:
                connectivity = service.check_connectivity()
                checks.append(("Database Connection", connectivity))

                if connectivity:
                    # Test basic operations
                    counts = service.get_node_counts()
                    checks.append(("Query Execution", True))
                    checks.append(("Node Count Query", counts is not None))
                else:
                    checks.append(("Query Execution", False))
                    checks.append(("Node Count Query", False))

        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            checks.append(("Database Connection", False))
            checks.append(("Query Execution", False))
            checks.append(("Node Count Query", False))

        # Display results
        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                console.print(f"[green]✓[/green] {check_name}")
            else:
                console.print(f"[red]✗[/red] {check_name}")
                all_passed = False

        if all_passed:
            console.print("\n[green]✓[/green] All graph database checks passed!")
            sys.exit(0)
        else:
            console.print("\n[red]✗[/red] Some graph database checks failed!")
            sys.exit(1)

    except ConfigurationError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error checking graph database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
