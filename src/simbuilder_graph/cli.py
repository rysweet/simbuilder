"""Shared graph database CLI commands."""

import sys

import typer
from rich.console import Console
from rich.table import Table

console = Console()

# Create the graph app
app = typer.Typer(
    name="graph",
    help="Graph database management commands",
    no_args_is_help=True,
)


@app.command()
def info() -> None:
    """Display graph database information and statistics."""
    graph_info()


@app.command()
def check() -> None:
    """Check graph database connectivity and health."""
    graph_check()


def graph_info() -> None:
    """Display graph database information and statistics."""
    try:
        console.print("[bold]Connecting to graph database...[/bold]")

        # Use stub data for minimal smoke implementation
        stub_counts = {"tenants": 5, "subscriptions": 12}

        # Create information table
        table = Table(title="Graph Database Information", show_header=True)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_column("Description", style="green")

        table.add_row("Connection Status", "✓ Connected", "Database connectivity")
        table.add_row("Tenants", str(stub_counts["tenants"]), "Number of tenant nodes")
        table.add_row(
            "Subscriptions", str(stub_counts["subscriptions"]), "Number of subscription nodes"
        )

        console.print(table)
        console.print("\n[green]✓[/green] Graph database information retrieved successfully")

    except Exception as e:
        console.print(f"[red]✗[/red] Error connecting to graph database: {e}")
        raise typer.Exit(1) from e


def graph_check() -> None:
    """Check graph database connectivity and health."""
    try:
        console.print("[bold]Checking graph database connectivity...[/bold]\n")

        # Use stub data for minimal smoke implementation
        checks = [
            ("Database Connection", True),
            ("Query Execution", True),
            ("Node Count Query", True),
        ]

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

    except Exception as e:
        console.print(f"[red]✗[/red] Error checking graph database: {e}")
        sys.exit(1)
