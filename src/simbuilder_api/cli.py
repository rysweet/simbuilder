"""
CLI commands for SimBuilder API service.
"""


import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from src.scaffolding.config import get_settings

from .main import create_app

app = typer.Typer(help="SimBuilder Core API service commands")
console = Console()


@app.command()
def run(
    host: str = typer.Option("localhost", help="Host to bind to"),
    port: int | None = typer.Option(None, help="Port to bind to (defaults to config)"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
    workers: int = typer.Option(1, help="Number of worker processes"),
) -> None:
    """Run the SimBuilder API server."""
    settings = get_settings()

    # Use port from settings if not specified
    if port is None:
        port = settings.core_api_port

    console.print("[bold green]Starting SimBuilder API server[/bold green]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")
    console.print(f"Environment: {settings.environment}")
    console.print(f"Debug mode: {settings.debug_mode}")

    try:
        uvicorn.run(
            "simbuilder_api.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level=settings.log_level.lower(),
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def info() -> None:
    """Display API service information."""
    settings = get_settings()

    table = Table(title="SimBuilder API Service Information")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Service Name", "SimBuilder Core API")
    table.add_row("Version", "1.0.0")
    table.add_row("Environment", settings.environment)
    table.add_row("API URL", settings.core_api_url)
    table.add_row("API Port", str(settings.core_api_port))
    table.add_row("Debug Mode", str(settings.debug_mode))
    table.add_row("Log Level", settings.log_level)
    table.add_row("JWT Secret", "***" if settings.jwt_secret else "Not set")

    # Health endpoints
    table.add_row("Health Check", f"{settings.core_api_url}/health/healthz")
    table.add_row("Readiness Check", f"{settings.core_api_url}/health/readyz")
    table.add_row("API Documentation", f"{settings.core_api_url}/docs")

    console.print(table)


@app.command()
def check() -> None:
    """Check API service configuration and dependencies."""
    settings = get_settings()

    console.print("[bold]Checking SimBuilder API configuration...[/bold]")

    # Check configuration
    issues = []

    if not settings.jwt_secret or settings.jwt_secret == "insecure-dev-secret":  # noqa: S105
        if settings.environment == "production":
            issues.append("JWT secret should be changed in production")
        else:
            console.print("⚠️  Using default JWT secret (OK for development)")

    if settings.core_api_port < 1024:
        issues.append("API port should be >= 1024 for non-root users")

    # Check if FastAPI app can be created
    try:
        create_app()
        console.print("✅ FastAPI application created successfully")
    except Exception as e:
        issues.append(f"Failed to create FastAPI app: {e}")

    # Check dependencies
    import importlib.util

    missing_deps = []
    for dep in ["fastapi", "jose", "uvicorn"]:
        if importlib.util.find_spec(dep) is None:
            missing_deps.append(dep)

    if missing_deps:
        error_msg = f"Missing dependencies: {', '.join(missing_deps)}"
        console.print(f"❌ {error_msg}")
        issues.append(error_msg)
    else:
        console.print("✅ Required dependencies available")

    # Report results
    if issues:
        console.print(f"[red]Found {len(issues)} issue(s):[/red]")
        for issue in issues:
            console.print(f"  ❌ {issue}")
        raise typer.Exit(1)
    else:
        console.print("[green]✅ All checks passed![/green]")


if __name__ == "__main__":
    app()
