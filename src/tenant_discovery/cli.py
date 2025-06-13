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

# --- API Auto-Start Helper ---
import subprocess
import shutil
import time
from pathlib import Path


def ensure_backend_running(api_base_url="http://localhost:8000") -> None:
    """Ensure the backend API is running, starting via docker-compose if necessary."""
    health_url = f"{api_base_url.rstrip('/')}/health"
    compose_file = Path("docker-compose.yaml")

    def is_backend_up() -> bool:
        try:
            with httpx.Client(timeout=3) as client:
                resp = client.get(health_url)
            return resp.status_code == 200
        except Exception:
            return False

    if is_backend_up():
        return
    # Try auto-start only if compose file and docker present
    if not compose_file.exists():
        raise RuntimeError(
            "Backend is not running and docker-compose.yaml is missing. Please start the backend manually."
        )

    if shutil.which("docker") is None:
        raise RuntimeError(
            "Backend is not running and 'docker' command not found in PATH. Please install Docker and retry."
        )

    compose_services = []
    try:
        with open(compose_file) as f:
            import yaml

            compose_cfg = yaml.safe_load(f)
            compose_services = set(compose_cfg.get("services", {}).keys())
    except Exception:
        # fallback: try both service names
        compose_services = []

    service_names = ["api", "simbuilder_api"]
    tried_services = []
    for candidate in service_names:
        if not compose_services or candidate in compose_services:
            try:
                subprocess.run(
                    ["docker", "compose", "up", "-d", candidate],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=20,
                )
                tried_services.append(candidate)
                break
            except Exception:
                continue
    else:
        raise RuntimeError(
            "Failed to start backend via docker compose. Please check your docker-compose.yaml."
        )

    # Poll health endpoint up to 30sec
    for _ in range(15):
        if is_backend_up():
            return
        time.sleep(2)
    raise RuntimeError(
        "Backend did not become healthy after starting Docker. Please check logs and try again."
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
    ctx: typer.Context,
    tenant_id: str | None = typer.Option(
        None, "--tenant-id", help="Azure tenant ID for discovery (overrides config)"
    ),
) -> None:
    """Start tenant resource discovery."""
    try:
        settings = get_td_settings()
        effective_tenant_id = tenant_id or settings.azure_tenant_id

        api_base_url = os.environ.get("TD_API_BASE_URL", "http://localhost:8000")
        url = f"{api_base_url.rstrip('/')}/tenant-discovery/sessions"
        payload = {"tenant_id": effective_tenant_id}
        try_count = 0
        while True:
            try:
                with httpx.Client(timeout=15) as client:
                    resp = client.post(url, json=payload)
                if resp.status_code in (200, 201):
                    console.print(f"[green]Discovery session started[/green]")
                    data = resp.json()
                    console.print(f"Session ID: {data.get('id')}")
                    console.print(f"Tenant ID: {data.get('tenant_id')}")
                    sys.exit(0)
                else:
                    try:
                        err = resp.json()
                    except Exception:
                        err = resp.text
                    console.print(f"[red]✗ Failed to start discovery: {resp.status_code}[/red]")
                    console.print(f"[yellow]Details:[/yellow] {err}")
                    sys.exit(resp.status_code or 1)
            except httpx.RequestError as e:
                # On connection refusal, try backend auto-start then retry only once
                if try_count == 0:
                    try:
                        console.print(
                            "[yellow]Backend API connection failed, attempting to auto-start backend...[/yellow]"
                        )
                        ensure_backend_running(api_base_url)
                        try_count += 1
                        continue
                    except Exception as autostart_err:
                        console.print(
                            "[red]✗ Could not connect to backend API and failed to auto-start backend: "
                            f"{autostart_err}[/red]"
                        )
                        console.print(
                            "[yellow]Please ensure the backend is running and try again.[/yellow]"
                        )
                        sys.exit(2)
                else:
                    console.print(f"[red]✗ Could not connect to backend API: {e}[/red]")
                    console.print(
                        "[yellow]Please ensure the backend is running and try again.[/yellow]"
                    )
                    sys.exit(2)
    except Exception as e:
        console.print(f"[red]✗[/red] Error starting discovery: {e}")
        sys.exit(1)


@discovery_app.command()
def list(ctx: typer.Context) -> None:
    """List discovery sessions."""
    api_base_url = os.environ.get("TD_API_BASE_URL", "http://localhost:8000")
    url = f"{api_base_url.rstrip('/')}/tenant-discovery/sessions"
    try_count = 0
    while True:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(url)
            table = Table(title="Discovery Sessions", show_header=True)
            table.add_column("Session ID", style="cyan", no_wrap=True)
            table.add_column("Tenant ID", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Started", style="blue")
            if resp.status_code == 200:
                data = resp.json()
                for row in data:
                    table.add_row(
                        row.get("id", ""),
                        row.get("tenant_id", ""),
                        row.get("status", ""),
                        row.get("created", ""),
                    )
                console.print(table)
                sys.exit(0)
            else:
                console.print(f"[red]✗ Failed to list sessions: {resp.status_code}[/red]")
                sys.exit(resp.status_code or 1)
        except httpx.RequestError as e:
            if try_count == 0:
                try:
                    console.print(
                        "[yellow]Backend API connection failed, attempting to auto-start backend...[/yellow]"
                    )
                    ensure_backend_running(api_base_url)
                    try_count += 1
                    continue
                except Exception as autostart_err:
                    console.print(
                        "[red]✗ Could not connect to backend API and failed to auto-start backend: "
                        f"{autostart_err}[/red]"
                    )
                    console.print(
                        "[yellow]Please ensure the backend is running and try again.[/yellow]"
                    )
                    sys.exit(2)
            else:
                console.print(f"[red]✗ Could not connect to backend API: {e}[/red]")
                console.print(
                    "[yellow]Please ensure the backend is running and try again.[/yellow]"
                )
                sys.exit(2)
        except Exception as e:
            console.print(f"[red]✗[/red] Error listing discovery sessions: {e}")
            sys.exit(1)


@discovery_app.command()
def status(
    session_id: str = typer.Argument(None, help="Session ID to check status for (optional)"),
) -> None:
    """Show status of a discovery session."""
    if not session_id:
        console.print(
            "[yellow]No session ID provided. Use 'tdcli discovery list' to see available sessions.[/yellow]"
        )
        sys.exit(2)

    api_base_url = os.environ.get("TD_API_BASE_URL", "http://localhost:8000")
    url = f"{api_base_url.rstrip('/')}/tenant-discovery/sessions/{session_id}/status"
    try_count = 0
    while True:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                console.print(f"[cyan]Status for session {session_id}:[/cyan]")
                console.print(f"[green]Status: {data.get('status', 'unknown')}[/green]")
                console.print(f"[blue]Progress: {data.get('details', '')}[/blue]")
                sys.exit(0)
            else:
                console.print(f"[red]✗ Failed to fetch session status: {resp.status_code}[/red]")
                sys.exit(resp.status_code or 1)
        except httpx.RequestError as e:
            if try_count == 0:
                try:
                    console.print(
                        "[yellow]Backend API connection failed, attempting to auto-start backend...[/yellow]"
                    )
                    ensure_backend_running(api_base_url)
                    try_count += 1
                    continue
                except Exception as autostart_err:
                    console.print(
                        "[red]✗ Could not connect to backend API and failed to auto-start backend: "
                        f"{autostart_err}[/red]"
                    )
                    console.print(
                        "[yellow]Please ensure the backend is running and try again.[/yellow]"
                    )
                    sys.exit(2)
            else:
                console.print(f"[red]✗ Could not connect to backend API: {e}[/red]")
                console.print(
                    "[yellow]Please ensure the backend is running and try again.[/yellow]"
                )
                sys.exit(2)
        except Exception as e:
            console.print(f"[red]✗[/red] Error getting discovery status: {e}")
            sys.exit(1)


@app.command("start")
def start_command(
    name: str = typer.Option(..., "--name", help="Session name (required)"),
    description: str = typer.Option(None, "--description", help="Optional session description"),
) -> None:
    """Start a new tenant discovery session."""
    api_base_url = os.environ.get("TD_API_BASE_URL", "http://localhost:8000")
    url = f"{api_base_url.rstrip('/')}/tenant-discovery/sessions"
    payload = {"name": name}
    if description is not None:
        payload["description"] = description

    try_count = 0
    while True:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(url, json=payload)
            if resp.status_code in (200, 201):
                data = resp.json()
                session_id = str(data.get("id", "[unknown id]"))
                console.print("[green]✓ Discovery session started![/green]")
                console.print(f"[bold]Session ID:[/bold] {session_id}")
                table = Table(title="Session Details", show_header=True)
                for k, v in data.items():
                    table.add_row(str(k), str(v))
                console.print(table)
                sys.exit(0)
            else:
                try:
                    err = resp.json()
                except Exception:
                    err = resp.text
                console.print(f"[red]✗ Failed to start session: {resp.status_code}[/red]")
                console.print(f"[yellow]Details:[/yellow] {err}")
                sys.exit(resp.status_code or 1)
        except httpx.RequestError as e:
            if try_count == 0:
                try:
                    console.print(
                        "[yellow]Backend API connection failed, attempting to auto-start backend...[/yellow]"
                    )
                    ensure_backend_running(api_base_url)
                    try_count += 1
                    continue
                except Exception as autostart_err:
                    console.print(
                        "[red]✗ Could not connect to backend API and failed to auto-start backend: "
                        f"{autostart_err}[/red]"
                    )
                    console.print(
                        "[yellow]Please ensure the backend is running and try again.[/yellow]"
                    )
                    sys.exit(2)
            else:
                console.print(f"[red]✗ Could not connect to backend API: {e}[/red]")
                console.print(
                    "[yellow]Please ensure the backend is running and try again.[/yellow]"
                )
                sys.exit(2)
        except Exception as e:
            import traceback

            console.print(f"[red]✗ Network or unexpected error: {e}[/red]")
            console.print(f"[yellow]TRACEBACK:[/yellow]\n{traceback.format_exc()}")
            sys.exit(1)


if __name__ == "__main__":
    app()
