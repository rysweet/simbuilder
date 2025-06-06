"""
CLI interface for SimBuilder scaffolding operations.
"""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import get_settings
from .exceptions import ConfigurationError
from .logging import setup_logging

app = typer.Typer(
    name="scaffolding",
    help="SimBuilder scaffolding utilities and health checks",
    add_completion=False,
)

console = Console()


@app.command()
def info() -> None:
    """Display loaded configuration and version information."""
    try:
        # Setup logging first
        logger = setup_logging()
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
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def check() -> None:
    """Perform health checks on configured services."""
    logger = setup_logging()
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
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {e}")
        logger.error("Health check failed with unexpected error", error=str(e))
        raise typer.Exit(1)


def _check_neo4j(settings) -> tuple[str, str]:
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


def _check_nats(settings) -> tuple[str, str]:
    """Check NATS connectivity."""
    try:
        # Import here to avoid dependency issues if NATS not available
        import nats

        async def check_connection():
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


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
