"""Tenant Discovery CLI interface."""

import sys

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from .config import get_td_settings

app = typer.Typer(
    name="tdcli",
    help="Tenant Discovery CLI",
    no_args_is_help=True,
)

# Create subcommands
config_app = typer.Typer(name="config", help="Configuration management commands")

app.add_typer(config_app, name="config")

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


if __name__ == "__main__":
    app()
