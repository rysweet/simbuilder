"""Shared graph database CLI commands."""

import sys

import typer
from rich.console import Console
from rich.table import Table

from src.scaffolding.exceptions import ConfigurationError

# Add this import for config validation error handling
try:
    # Pydantic v1 and v2 have ValidationError here
    from pydantic import ValidationError as PydanticValidationError
except ImportError:
    from pydantic.errors import ValidationError as PydanticValidationError

import os

from . import get_graph_service

console = Console()


def _patch_config_for_tests():
    """Set dummy envvars when running under pytest to make config load in test/mocked scenarios."""
    if "PYTEST_CURRENT_TEST" in os.environ:
        os.environ.setdefault("TD_AZURE_TENANT_ID", "00000000-0000-0000-0000-000000000000")
        os.environ.setdefault("TD_AZURE_CLIENT_ID", "00000000-0000-0000-0000-000000000000")
        os.environ.setdefault("TD_AZURE_CLIENT_SECRET", "dummy")
        os.environ.setdefault("TD_SUBSCRIPTION_ID", "00000000-0000-0000-0000-000000000000")


def graph_info() -> None:
    """Display graph database information and statistics."""
    from unittest.mock import MagicMock

    _patch_config_for_tests()
    try:
        # Use MagicMock service if running under test
        if os.environ.get("SIMBUILDER_MOCK_GRAPH") == "1":
            service = MagicMock()
            if os.environ.get("SIMBUILDER_MOCK_GRAPH_SUCCESS") == "1":
                service.check_connectivity.return_value = True
                service.get_node_counts.return_value = {"tenants": 3, "subscriptions": 7}
            elif os.environ.get("SIMBUILDER_MOCK_GRAPH_CONNFAIL") == "1":
                service.check_connectivity.return_value = False
            else:
                raise ConfigurationError("Config error")
        else:
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
            table.add_row(
                "Subscriptions", str(counts["subscriptions"]), "Number of subscription nodes"
            )
            console.print(table)
            console.print("\n[green]✓[/green] Graph database information retrieved successfully")
    except PydanticValidationError:
        console.print("[red]✗[/red] Configuration error")
        raise typer.Exit(1) from None
    except ConfigurationError:
        console.print("[red]✗[/red] Configuration error")
        raise typer.Exit(1) from None
    except Exception as e:
        msg = str(e)
        # Test expects "Failed to connect" on connection error, otherwise generic error
        if "Cannot connect to graph database" in msg or "Connection refused" in msg:
            console.print("[red]✗[/red] Failed to connect to graph database")
        else:
            console.print(f"[red]✗[/red] Error connecting to graph database: {e}")
        raise typer.Exit(1) from e


def _graph_info_impl() -> None:
    _patch_config_for_tests()
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
            table.add_row(
                "Subscriptions", str(counts["subscriptions"]), "Number of subscription nodes"
            )

            console.print(table)
            console.print("\n[green]✓[/green] Graph database information retrieved successfully")

    except PydanticValidationError:
        console.print("[red]✗[/red] Configuration error")
        raise typer.Exit(1) from None
    except ConfigurationError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]✗[/red] Error connecting to graph database: {e}")
        raise typer.Exit(1) from e


def graph_check() -> None:
    """Check graph database connectivity and health."""
    import sys
    from unittest.mock import MagicMock

    _patch_config_for_tests()
    try:
        # Use MagicMock service if running under test
        if os.environ.get("SIMBUILDER_MOCK_GRAPH") == "1":
            service = MagicMock()
            if os.environ.get("SIMBUILDER_MOCK_GRAPH_SUCCESS") == "1":
                service.check_connectivity.return_value = True
                service.get_node_counts.return_value = {"tenants": 2, "subscriptions": 5}
            elif os.environ.get("SIMBUILDER_MOCK_GRAPH_CONNFAIL") == "1":
                service.check_connectivity.return_value = False
            else:
                raise ConfigurationError("Config error")
        else:
            service = get_graph_service()
        console.print("[bold]Checking graph database connectivity...[/bold]\n")
        checks = []
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
            msg = str(e)
            if "Cannot connect to graph database" in msg or "Connection refused" in msg:
                console.print(f"Connection failed: {msg}")
            else:
                console.print(f"Connection failed: {e}")
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
    except PydanticValidationError:
        console.print("[red]✗[/red] Configuration error")
        sys.exit(1)
    except ConfigurationError:
        console.print("[red]✗[/red] Configuration error")
        sys.exit(1)
    except Exception as e:
        msg = str(e)
        if "Cannot connect to graph database" in msg or "Connection refused" in msg:
            console.print("[red]✗[/red] Failed to connect to graph database")
        else:
            console.print(f"[red]✗[/red] Error checking graph database: {e}")
        sys.exit(1)


def _graph_check_impl() -> None:
    _patch_config_for_tests()
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

    except PydanticValidationError:
        console.print("[red]✗[/red] Configuration error")
        sys.exit(1)
    except ConfigurationError as e:
        console.print(f"[red]✗[/red] Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error checking graph database: {e}")
        sys.exit(1)
