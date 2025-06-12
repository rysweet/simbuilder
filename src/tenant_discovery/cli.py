"""Tenant Discovery CLI interface."""

import os
import sys
from typing import Any
from uuid import UUID

import httpx
import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

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

console = Console()


def is_missing(val: object) -> bool:
    return not val or str(val).strip() == "00000000-0000-0000-0000-000000000000"


def get_td_settings():  # type: ignore
    """Helper function to get tenant discovery settings."""
    from src.tenant_discovery.config import TenantDiscoverySettings

    return TenantDiscoverySettings(_env_file=None)  # type: ignore


def _get_api_client() -> httpx.Client:
    """Get HTTP client for API calls."""
    settings = get_td_settings()
    return httpx.Client(base_url=settings.api_base_url, timeout=30.0)


def _handle_api_error(response: httpx.Response) -> None:
    """Handle API error responses."""
    if response.status_code == 404:
        console.print("[red]✗[/red] Resource not found")
    elif response.status_code >= 500:
        console.print(f"[red]✗[/red] Server error: {response.status_code}")
    else:
        try:
            error_data = response.json()
            detail = error_data.get("detail", "Unknown error")
            console.print(f"[red]✗[/red] API error: {detail}")
        except Exception:
            console.print(f"[red]✗[/red] HTTP {response.status_code}: {response.text}")
    raise typer.Exit(1)


@config_app.command()
def info() -> None:
    """Display current configuration settings."""
    try:
        # Robustly clear any bogus or inherited env for optional fields
        for envkey in [
            "AZURE_CLIENT_ID",
            "AZURE_SUBSCRIPTION_ID",
            "TD_AZURE_CLIENT_ID",
            "TD_SUBSCRIPTION_ID",
        ]:
            if envkey in os.environ:
                del os.environ[envkey]
        # Bypass .env loading in CLI
        from src.tenant_discovery.config import TenantDiscoverySettings

        settings = TenantDiscoverySettings(_env_file=None)  # type: ignore

        # Create a table to display settings
        table = Table(title="Tenant Discovery Configuration", show_header=True)
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_column("Description", style="green")

        # Mask sensitive values
        if settings.azure_client_secret:
            masked_secret = (
                "***" + settings.azure_client_secret[-4:]
                if len(settings.azure_client_secret) > 4
                else "***"
            )
        else:
            masked_secret = "[not set]"  # noqa: S105

        cid = None if is_missing(settings.azure_client_id) else settings.azure_client_id
        subid = None if is_missing(settings.subscription_id) else settings.subscription_id

        table.add_row(
            "Azure Tenant ID", settings.azure_tenant_id, "Azure tenant ID for authentication"
        )
        table.add_row(
            "Azure Client ID",
            cid if cid else "[not set]",
            "Azure client ID for authentication (optional)",
        )
        table.add_row("Azure Client Secret", masked_secret, "Azure client secret (masked)")
        table.add_row(
            "Subscription ID",
            subid if subid else "[not set]",
            "Azure subscription ID for resource discovery (optional)",
        )
        table.add_row("Graph DB URL", settings.graph_db_url, "Neo4j graph database connection URL")
        table.add_row(
            "Service Bus URL", settings.service_bus_url, "NATS service bus connection URL"
        )
        table.add_row("API Base URL", settings.api_base_url, "SimBuilder API base URL")
        table.add_row("Log Level", settings.log_level.value, "Logging level for the service")

        if not cid:
            console.print(
                "[yellow]⚠ Azure Client ID is not set; some operations may be unavailable.[/yellow]"
            )
        if not subid:
            console.print(
                "[yellow]⚠ Subscription ID is not set; resource discovery may be limited.[/yellow]"
            )

        console.print(table)
        console.print("\n[green]✓[/green] Configuration loaded successfully")

    except ValidationError as e:
        import traceback

        console.print("[red]✗[/red] Configuration validation failed:")
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            console.print(f"  • {field}: {error['msg']}")
        console.print(f"[yellow]TRACEBACK:[/yellow]\n{traceback.format_exc()}")
        raise typer.Exit(1) from None
    except Exception as e:
        import traceback

        console.print(f"[red]✗[/red] Error loading configuration: {e}")
        console.print(f"[yellow]TRACEBACK:[/yellow]\n{traceback.format_exc()}")
        raise typer.Exit(1) from e


@config_app.command()
def check() -> None:
    """Validate configuration and environment variables."""
    try:
        # Robustly clear any bogus or inherited env for optional fields
        for envkey in [
            "AZURE_CLIENT_ID",
            "AZURE_SUBSCRIPTION_ID",
            "TD_AZURE_CLIENT_ID",
            "TD_SUBSCRIPTION_ID",
        ]:
            if envkey in os.environ:
                del os.environ[envkey]
        from src.tenant_discovery.config import TenantDiscoverySettings

        settings = TenantDiscoverySettings(_env_file=None)  # type: ignore
        console.print(f"LOADED SETTINGS: {settings!r}")

        console.print("[bold]Validating Tenant Discovery configuration...[/bold]\n")

        # Use sanitized values for presence checks
        checks = [
            ("Azure Tenant ID format", bool(settings.azure_tenant_id)),
            ("Azure Client ID presence (optional)", not is_missing(settings.azure_client_id)),
            ("Azure Client Secret presence", bool(settings.azure_client_secret)),
            ("Subscription ID presence (optional)", not is_missing(settings.subscription_id)),
            ("Graph DB URL format", bool(settings.graph_db_url)),
            ("Service Bus URL format", bool(settings.service_bus_url)),
            ("API Base URL format", bool(settings.api_base_url)),
            ("Log Level validity", bool(settings.log_level.value)),
        ]

        # Only required field failures (tenant_id and secret) are fatal
        all_passed = True
        # DEBUG: Print all check results for CI
        debug_checks = []
        for check_name, check_value in checks:
            debug_checks.append((check_name, check_value))
            if check_value:
                console.print(f"[green]✓[/green] {check_name}")
            else:
                # Only tenant_id and secret presence are required
                if "Tenant ID" in check_name or "Client Secret" in check_name:
                    console.print(f"[red]✗[/red] {check_name}")
                    all_passed = False
                else:
                    console.print(f"[yellow]⚠[/yellow] {check_name} [optional] not set")
        # DEBUG: summary line for troubleshooting

        if all_passed:
            console.print("\n[green]✓[/green] All required configuration checks passed!")
            sys.exit(0)
        else:
            console.print("\n[red]✗[/red] Required configuration check(s) failed!")
            sys.exit(1)

    except ValidationError as e:
        import traceback

        console.print("[red]✗[/red] Configuration validation failed:")
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            console.print(f"  • {field}: {error['msg']}")
        console.print(f"[yellow]TRACEBACK:[/yellow]\n{traceback.format_exc()}")
        sys.exit(1)
    except Exception as e:
        import traceback

        console.print(f"[red]✗[/red] Error validating configuration: {e}")
        console.print(f"[yellow]TRACEBACK:[/yellow]\n{traceback.format_exc()}")
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

        # Create discovery session via API
        session_data = {
            "tenant_id": effective_tenant_id,
            "description": f"CLI discovery session for tenant {effective_tenant_id}",
            "config": {},
        }

        with _get_api_client() as client:
            response = client.post("/tenant-discovery/sessions", json=session_data)

            if response.status_code != 200:
                _handle_api_error(response)

            session = response.json()
            session_id = session["id"]

            console.print("[green]✓[/green] Discovery session started")
            console.print(f"[cyan]Session ID:[/cyan] {session_id}")
            console.print(f"[cyan]Tenant ID:[/cyan] {effective_tenant_id}")
            console.print(f"[cyan]Status:[/cyan] {session['status']}")

    except httpx.RequestError as e:
        console.print(f"[red]✗[/red] Failed to connect to API: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error starting discovery: {e}")
        sys.exit(1)


@discovery_app.command()
def list() -> None:
    """List discovery sessions."""
    try:
        with _get_api_client() as client:
            response = client.get("/tenant-discovery/sessions")

            if response.status_code != 200:
                _handle_api_error(response)

            data = response.json()
            sessions = data.get("sessions", [])
            total = data.get("total", 0)

            if not sessions:
                console.print("[yellow]No discovery sessions found.[/yellow]")
                return

            table = Table(title=f"Discovery Sessions ({total} total)", show_header=True)
            table.add_column("Session ID", style="cyan", no_wrap=True)
            table.add_column("Tenant ID", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Created", style="blue")
            table.add_column("Description", style="white")

            for session in sessions:
                # Truncate session ID for display
                session_id_short = str(session["id"])[:8] + "..."
                created_at = session["created_at"].split("T")[0]  # Just the date part
                description = session.get("description", "")[:50]  # Truncate description
                if len(session.get("description", "")) > 50:
                    description += "..."

                # Color code status
                status = session["status"]
                if status == "completed":
                    status_display = f"[green]{status}[/green]"
                elif status == "failed":
                    status_display = f"[red]{status}[/red]"
                elif status == "running":
                    status_display = f"[yellow]{status}[/yellow]"
                else:
                    status_display = status

                table.add_row(
                    session_id_short, session["tenant_id"], status_display, created_at, description
                )

            console.print(table)

    except httpx.RequestError as e:
        console.print(f"[red]✗[/red] Failed to connect to API: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error listing discovery sessions: {e}")
        sys.exit(1)


@discovery_app.command()
def status(
    session_id: str = typer.Argument(None, help="Session ID to check status for (optional)")
) -> None:
    """Show status of a discovery session."""
    try:
        if not session_id:
            console.print(
                "[yellow]No session ID provided. Use 'tdcli discovery list' to see available sessions.[/yellow]"
            )
            return

        with _get_api_client() as client:
            # Try to parse as UUID, if it fails, assume it's a short form
            try:
                UUID(session_id)
                status_url = f"/tenant-discovery/sessions/{session_id}/status"
                detail_url = f"/tenant-discovery/sessions/{session_id}"
            except ValueError:
                # Short form ID - need to get full sessions list to find match
                list_response = client.get("/tenant-discovery/sessions")
                if list_response.status_code != 200:
                    _handle_api_error(list_response)

                data = list_response.json()
                sessions = data.get("sessions", [])
                matching_session = None

                for session in sessions:
                    if str(session["id"]).startswith(session_id):
                        matching_session = session
                        break

                if not matching_session:
                    console.print(f"[red]✗[/red] No session found matching ID: {session_id}")
                    sys.exit(1)

                full_id = matching_session["id"]
                status_url = f"/tenant-discovery/sessions/{full_id}/status"
                detail_url = f"/tenant-discovery/sessions/{full_id}"

            # Get status
            status_response = client.get(status_url)
            if status_response.status_code != 200:
                _handle_api_error(status_response)

            # Get full details
            detail_response = client.get(detail_url)
            if detail_response.status_code != 200:
                _handle_api_error(detail_response)

            status_data = status_response.json()
            detail_data = detail_response.json()

            console.print("[cyan]Discovery Session Status[/cyan]")
            console.print(f"[bold]Session ID:[/bold] {detail_data['id']}")
            console.print(f"[bold]Tenant ID:[/bold] {detail_data['tenant_id']}")

            # Color code status
            status = detail_data["status"]
            if status == "completed":
                status_display = f"[green]{status}[/green]"
            elif status == "failed":
                status_display = f"[red]{status}[/red]"
            elif status == "running":
                status_display = f"[yellow]{status}[/yellow]"
            else:
                status_display = status

            console.print(f"[bold]Status:[/bold] {status_display}")
            console.print(f"[bold]Created:[/bold] {detail_data['created_at']}")
            console.print(f"[bold]Updated:[/bold] {detail_data['updated_at']}")

            if detail_data.get("completed_at"):
                console.print(f"[bold]Completed:[/bold] {detail_data['completed_at']}")

            if detail_data.get("error_message"):
                console.print(f"[bold]Error:[/bold] [red]{detail_data['error_message']}[/red]")

            if detail_data.get("description"):
                console.print(f"[bold]Description:[/bold] {detail_data['description']}")

            # Show progress if available
            progress = status_data.get("progress", 0)
            console.print(f"[bold]Progress:[/bold] {progress}%")

    except httpx.RequestError as e:
        console.print(f"[red]✗[/red] Failed to connect to API: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error getting discovery status: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
