"""
CLI interface for SimBuilder scaffolding operations.
"""

import asyncio
from typing import Any
from typing import cast

import typer
from rich.console import Console
from rich.table import Table

# Use type: ignore for modules that may not exist
from simbuilder_api.cli import app as api_cli_app  # type: ignore[import-not-found]
from simbuilder_graph.cli import graph_check  # type: ignore[import-not-found]
from simbuilder_graph.cli import graph_info
from simbuilder_llm.cli import app as llm_cli_app  # type: ignore[import-not-found]
from simbuilder_servicebus.cli import app as servicebus_cli_app  # type: ignore[import-not-found]
from simbuilder_specs.cli import app as specs_cli_app  # type: ignore[import-not-found]

from . import __version__
from .config import get_settings
from .exceptions import ConfigurationError
from .logging import setup_logging
from .session import SessionManager

app = typer.Typer(
    name="scaffolding",
    help="SimBuilder scaffolding utilities and health checks",
    add_completion=False,
)

# Create session subcommand group
session_app = typer.Typer(
    name="session",
    help="Session management commands",
    add_completion=False,
)
app.add_typer(session_app, name="session")

# Create graph subcommand group
graph_app = typer.Typer(
    name="graph",
    help="Graph database commands",
    add_completion=False,
)
app.add_typer(graph_app, name="graph")

# Create servicebus subcommand group
servicebus_app = typer.Typer(
    name="servicebus",
    help="Service Bus messaging commands",
    add_completion=False,
)
app.add_typer(servicebus_app, name="servicebus")

# Create specs subcommand group
specs_app = typer.Typer(
    name="specs",
    help="Spec Library management commands",
    add_completion=False,
)
app.add_typer(specs_app, name="specs")

# Create api subcommand group
api_app = typer.Typer(
    name="api",
    help="Core API service commands",
    add_completion=False,
)
app.add_typer(api_app, name="api")

# Create llm subcommand group
llm_app = typer.Typer(
    name="llm",
    help="LLM integration commands",
    add_completion=False,
)
app.add_typer(llm_app, name="llm")

console = Console()


@app.command()
def info() -> None:
    """Display loaded configuration and version information."""
    try:
        # Setup logging first
        logger = setup_logging()

        # Try to get current session info
        session_id = _get_current_session_id()
        if session_id:
            logger.info("Displaying scaffolding information", session_id=session_id)
        else:
            logger.info("Displaying scaffolding information")

        # Load settings
        settings = get_settings()

        console.print(f"\n[bold green]SimBuilder Scaffolding v{__version__}[/bold green]")
        console.print("=" * 50)

        # Create configuration table
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="magenta")

        # Add configuration values (masking sensitive data)
        config_data = [
            ("Environment", settings.environment),
            ("Log Level", settings.log_level),
            ("Debug Mode", str(settings.debug_mode)),
            ("Azure Tenant ID", settings.azure_tenant_id),
            ("Neo4j URI", settings.neo4j_uri),
            ("Neo4j Database", settings.neo4j_database),
            ("Service Bus URL", settings.service_bus_url),
            ("Core API URL", settings.core_api_url),
            ("Core API Port", str(settings.core_api_port)),
            ("Azure OpenAI Endpoint", settings.azure_openai_endpoint),
            ("OpenAI API Version", settings.azure_openai_api_version),
            ("Chat Model", settings.azure_openai_model_chat),
            ("Reasoning Model", settings.azure_openai_model_reasoning),
        ]

        for setting, value in config_data:
            config_table.add_row(setting, value)

        console.print(config_table)

        # Show masked sensitive values
        console.print("\n[dim]Sensitive values are displayed but not their actual content:[/dim]")
        sensitive_table = Table()
        sensitive_table.add_column("Setting", style="yellow")
        sensitive_table.add_column("Status", style="green")

        sensitive_data = [
            ("Neo4j Password", "Set" if settings.neo4j_password else "Not Set"),
            ("Azure OpenAI Key", "Set" if settings.azure_openai_key else "Not Set"),
            ("Azure Client Secret", "Set" if settings.azure_client_secret else "Not Set"),
        ]

        for setting, status in sensitive_data:
            sensitive_table.add_row(setting, status)

        console.print(sensitive_table)

    except ConfigurationError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        raise typer.Exit(1) from e


@app.command()
def check() -> None:
    """Perform health checks on configured services."""
    logger = setup_logging()

    # Try to get current session info
    session_id = _get_current_session_id()
    if session_id:
        logger.info("Starting health checks", session_id=session_id)
    else:
        logger.info("Starting health checks")

    try:
        settings = get_settings()

        console.print("\n[bold blue]SimBuilder Health Check[/bold blue]")
        console.print("=" * 40)

        # Create results table
        results_table = Table(title="Service Health Check Results")
        results_table.add_column("Service", style="cyan")
        results_table.add_column("Status", style="bold")
        results_table.add_column("Details", style="dim")

        checks = []

        # Configuration check
        try:
            settings.validate_required_for_environment()
            checks.append(("Configuration", "[green]✓ OK[/green]", "All required settings present"))
        except ConfigurationError as e:
            checks.append(("Configuration", "[red]✗ FAIL[/red]", str(e)))

        # Neo4j check (if configured)
        if settings.neo4j_password:
            neo4j_status = _check_neo4j(settings)
            checks.append(("Neo4j", neo4j_status[0], neo4j_status[1]))
        else:
            checks.append(("Neo4j", "[yellow]⚠ SKIP[/yellow]", "Password not configured"))

        # NATS check
        nats_status = _check_nats(settings)
        checks.append(("NATS/Service Bus", nats_status[0], nats_status[1]))

        # Add all results to table
        for service, status, details in checks:
            results_table.add_row(service, status, details)

        console.print(results_table)

        # Count failures
        failures = sum(1 for _, status, _ in checks if "FAIL" in status)

        if failures > 0:
            console.print(f"\n[red]{failures} check(s) failed.[/red]")
            logger.error("Health check completed with failures", failed_count=failures)
            raise typer.Exit(1)
        else:
            console.print("\n[green]All checks passed![/green]")
            logger.info("Health check completed successfully")

    except ConfigurationError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        logger.error("Health check failed with unexpected error", error=str(e))
        raise typer.Exit(1) from e


def _check_neo4j(settings: Any) -> tuple[str, str]:
    """Check Neo4j connectivity."""
    try:
        # Import here to avoid dependency issues if Neo4j not available
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

        with driver.session(database=settings.neo4j_database) as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()
            if record and record["test"] == 1:
                driver.close()
                return "[green]✓ OK[/green]", "Connection successful"
            else:
                driver.close()
                return "[red]✗ FAIL[/red]", "Invalid response from database"

    except ImportError:
        return "[yellow]⚠ SKIP[/yellow]", "Neo4j driver not installed"
    except Exception as e:
        return "[red]✗ FAIL[/red]", f"Connection failed: {str(e)[:50]}..."


def _check_nats(settings: Any) -> tuple[str, str]:
    """Check NATS connectivity."""
    try:
        # Import here to avoid dependency issues if NATS not available
        import nats

        async def check_connection() -> tuple[bool, str]:
            try:
                nc = await nats.connect(settings.service_bus_url)
                await nc.close()
                return True, "Connection successful"
            except Exception as e:
                return False, f"Connection failed: {str(e)[:50]}..."

        # Run async check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success, message = loop.run_until_complete(check_connection())
            if success:
                return "[green]✓ OK[/green]", message
            else:
                return "[red]✗ FAIL[/red]", message
        finally:
            loop.close()

    except ImportError:
        return "[yellow]⚠ SKIP[/yellow]", "NATS client not installed"
    except Exception as e:
        return "[red]✗ FAIL[/red]", f"Check failed: {str(e)[:50]}..."


@session_app.command()
def create(
    services: str | None = typer.Option(
        None,
        "--services",
        help="Comma-separated list of services to allocate ports for"
    ),
    start_containers: bool = typer.Option(
        False,
        "--start-containers",
        help="Start Docker Compose containers after creating session"
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        help="Docker Compose profile to use when starting containers"
    )
) -> None:
    """Create a new SimBuilder session with dynamic port allocation."""
    try:
        logger = setup_logging()
        session_manager = SessionManager()

        # Parse services list if provided
        services_list = None
        if services:
            services_list = [s.strip() for s in services.split(",")]

        # Create the session
        session_info = session_manager.create_session(services_list)

        console.print("\n[bold green]* New SimBuilder session created![/bold green]")
        console.print("=" * 50)

        # Create session details table
        details_table = Table(title="Session Details")
        details_table.add_column("Property", style="cyan")
        details_table.add_column("Value", style="magenta")

        details_table.add_row("Session ID", session_info["session_id"])
        details_table.add_row("Short ID", session_info["session_short"])
        details_table.add_row("Compose Project", session_info["compose_project_name"])
        details_table.add_row("Created At", session_info["created_at"])
        details_table.add_row("Environment File", session_info["env_file_path"])

        console.print(details_table)

        # Create ports table
        ports_table = Table(title="Allocated Ports")
        ports_table.add_column("Service", style="cyan")
        ports_table.add_column("Port", style="green")

        allocated_ports = cast(dict[str, Any], session_info.get("allocated_ports", {}))
        if isinstance(allocated_ports, dict):
            for service, port in allocated_ports.items():
                ports_table.add_row(service, str(port))

        console.print(ports_table)

        console.print(f"\n[dim]Environment variables written to: {session_info['env_file_path']}[/dim]")
        console.print("[dim]Use 'source .env.session' to load environment variables[/dim]")

        # Start containers if requested
        if start_containers:
            console.print("\n[bold yellow]Starting Docker Compose containers...[/bold yellow]")

            success = session_manager.compose_up(detached=True, profile=profile)

            if success:
                console.print("[green]* Docker Compose services started successfully![/green]")
                console.print(f"[dim]Use 'docker compose -p {session_info['compose_project_name']} logs' to view logs[/dim]")
            else:
                console.print("[red]X Failed to start Docker Compose services[/red]")
                console.print("[dim]Check the logs above for more details[/dim]")
        else:
            console.print("\n[dim]To start containers manually, run:[/dim]")
            console.print(f"[dim]  docker compose -p {session_info['compose_project_name']} --env-file .env.session up -d[/dim]")

        logger.info(
            "Session creation completed via CLI",
            session_id=session_info["session_id"],
            containers_started=start_containers
        )

    except Exception as e:
        logger = setup_logging()
        logger.error("Session creation failed", error=str(e))
        console.print(f"[red]Error creating session:[/red] {e}")
        raise typer.Exit(1) from e


@session_app.command()
def list() -> None:
    """List all existing SimBuilder sessions."""
    try:
        logger = setup_logging()
        session_manager = SessionManager()

        sessions = session_manager.list_sessions()

        if not sessions:
            console.print("[yellow]No sessions found.[/yellow]")
            return

        console.print(f"\n[bold blue]SimBuilder Sessions ({len(sessions)} found)[/bold blue]")
        console.print("=" * 50)

        # Create sessions table
        sessions_table = Table()
        sessions_table.add_column("Session ID", style="cyan")
        sessions_table.add_column("Short ID", style="magenta")
        sessions_table.add_column("Compose Project", style="green")
        sessions_table.add_column("Created", style="dim")
        sessions_table.add_column("Services", style="yellow")

        for session in sessions:
            created_at = session.get("created_at", "Unknown")
            if "T" in created_at:
                created_at = created_at.split("T")[0]  # Show just the date

            services_count = len(session.get("services", []))

            sessions_table.add_row(
                session["session_id"][:8] + "...",
                session["session_short"],
                session["compose_project_name"],
                created_at,
                f"{services_count} services"
            )

        console.print(sessions_table)

        logger.info("Listed sessions via CLI", session_count=len(sessions))

    except Exception as e:
        logger = setup_logging()
        logger.error("Session listing failed", error=str(e))
        console.print(f"[red]Error listing sessions:[/red] {e}")
        raise typer.Exit(1) from e


@session_app.command()
def status(session_id: str) -> None:
    """Show status information for a specific session."""
    try:
        logger = setup_logging()
        session_manager = SessionManager()

        session_info = session_manager.get_session_status(session_id)

        if not session_info:
            console.print(f"[red]Session not found:[/red] {session_id}")
            raise typer.Exit(1)

        console.print(f"\n[bold blue]Session Status: {session_info['session_short']}[/bold blue]")
        console.print("=" * 50)

        # Create status table
        status_table = Table(title="Session Information")
        status_table.add_column("Property", style="cyan")
        status_table.add_column("Value", style="magenta")

        status_table.add_row("Session ID", session_info["session_id"])
        status_table.add_row("Short ID", session_info["session_short"])
        status_table.add_row("Compose Project", session_info["compose_project_name"])
        status_table.add_row("Created At", session_info["created_at"])
        status_table.add_row("Environment File", session_info["env_file_path"])
        status_table.add_row("Env File Exists", "* Yes" if session_info.get("env_file_exists") else "X No")
        status_table.add_row("Containers Running", "* Yes" if session_info.get("containers_running") else "X No")

        console.print(status_table)

        # Show allocated ports
        if "allocated_ports" in session_info:
            ports_table = Table(title="Allocated Ports")
            ports_table.add_column("Service", style="cyan")
            ports_table.add_column("Port", style="green")

            allocated_ports = cast(dict[str, Any], session_info.get("allocated_ports", {}))
            if isinstance(allocated_ports, dict):
                for service, port in allocated_ports.items():
                    ports_table.add_row(service, str(port))

            console.print(ports_table)

        logger.info(
            "Displayed session status via CLI",
            session_id=session_id
        )

    except Exception as e:
        logger = setup_logging()
        logger.error("Session status check failed", error=str(e), session_id=session_id)
        console.print(f"[red]Error getting session status:[/red] {e}")
        raise typer.Exit(1) from e


@session_app.command()
def cleanup(session_id: str) -> None:
    """Clean up a session by stopping containers and removing files."""
    try:
        logger = setup_logging()
        session_manager = SessionManager()

        # Get session info first
        session_info = session_manager.get_session_status(session_id)
        if not session_info:
            console.print(f"[red]Session not found:[/red] {session_id}")
            raise typer.Exit(1)

        console.print(f"\n[yellow]Cleaning up session: {session_info['session_short']}[/yellow]")

        # Perform cleanup
        success = session_manager.cleanup_session(session_id)

        if success:
            console.print("[green]* Session cleanup completed successfully![/green]")
            console.print(f"[dim]- Stopped containers for project: {session_info['compose_project_name']}[/dim]")
            console.print("[dim]- Removed session files and directories[/dim]")
            console.print("[dim]- Freed allocated ports[/dim]")
        else:
            console.print("[red]X Session cleanup failed![/red]")
            raise typer.Exit(1)

        logger.info(
            "Session cleanup completed via CLI",
            session_id=session_id
        )

    except Exception as e:
        logger = setup_logging()
        logger.error("Session cleanup failed", error=str(e), session_id=session_id)
        console.print(f"[red]Error cleaning up session:[/red] {e}")
        raise typer.Exit(1) from e


def _get_current_session_id() -> str | None:
    """
    Get the current session ID from environment or .env.session file.
    Returns:
        Session ID if found, None otherwise
    """
    import os

    from .config import get_project_root

    # Check environment variable first
    session_id = os.getenv("SIMBUILDER_SESSION_ID")
    if session_id:
        return session_id

    # Check .env.session file
    try:
        env_session_path = get_project_root() / ".env.session"
        if env_session_path.exists():
            with env_session_path.open(encoding='utf-8') as f:
                for line in f:
                    if line.startswith("SIMBUILDER_SESSION_ID="):
                        return line.split("=", 1)[1].strip()
    except Exception as e:
        import logging
        logging.getLogger("scaffolding.cli").warning(f"Could not read session ID from .env.session: {e}")

    return None



graph_app.command("info")(graph_info)
graph_app.command("check")(graph_check)
servicebus_app.add_typer(servicebus_cli_app, name="")
specs_app.add_typer(specs_cli_app, name="")
api_app.add_typer(api_cli_app, name="")
llm_app.add_typer(llm_cli_app, name="")


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
