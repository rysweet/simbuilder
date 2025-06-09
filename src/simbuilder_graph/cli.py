"""Shared graph database CLI commands."""

import sys

import typer
from rich.console import Console
from rich.table import Table

from src.scaffolding.exceptions import ConfigurationError

from . import get_graph_service

console = Console()


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
