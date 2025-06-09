"""
Project automation tasks using Invoke.
"""

import sys
from pathlib import Path

from invoke import task


@task
def bootstrap(ctx):
    """Bootstrap the development environment."""
    print("🚀 Bootstrapping SimBuilder development environment...")

    # Check if uv is installed
    if not ctx.run("where uv", warn=True, hide=True).ok:
        print("❌ uv is not installed. Please install uv first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

    # Create virtual environment
    print("📦 Creating virtual environment...")
    ctx.run("uv venv .venv --python 3.12")

    # Install dependencies
    print("📥 Installing dependencies...")
    ctx.run("uv pip install -r requirements.txt")

    # Install development dependencies
    print("🔧 Installing development dependencies...")
    dev_deps = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "ruff>=0.1.6",
        "mypy>=1.7.0",
        "black>=23.10.0",
        "pre-commit>=3.5.0",
        "mdformat>=0.7.17",
        "invoke>=2.2.0"
    ]
    ctx.run(f"uv pip install {' '.join(dev_deps)}")

    # Install pre-commit hooks
    print("🪝 Installing pre-commit hooks...")
    ctx.run("uv run pre-commit install")

    # Create .env from template if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file from template...")
        ctx.run("python -c \"from src.scaffolding.config import create_env_template; create_env_template()\"")
        print("⚠️  Please edit .env file with your configuration before running services!")

    print("✅ Bootstrap complete! Don't forget to:")
    print("   1. Edit .env file with your configuration")
    print("   2. Run 'invoke start-infra' to start infrastructure services")
    print("   3. Run 'invoke test' to verify everything works")


@task
def lint(ctx):
    """Run linting and code quality checks."""
    print("🔍 Running linting checks...")

    print("📋 Running ruff...")
    ctx.run("uv run ruff check src/ tests/")

    print("🎨 Running black...")
    ctx.run("uv run black --check src/ tests/")

    print("🔧 Running mypy...")
    ctx.run("uv run mypy src/")

    print("✅ All linting checks passed!")


@task
def format(ctx):
    """Format code using ruff and black."""
    print("🎨 Formatting code...")

    print("📋 Running ruff formatter...")
    ctx.run("uv run ruff format src/ tests/")

    print("🎨 Running black...")
    ctx.run("uv run black src/ tests/")

    print("✅ Code formatting complete!")


@task
def test(ctx, coverage=False):
    """Run tests."""
    print("🧪 Running tests...")

    cmd = "uv run pytest tests/ -v"
    if coverage:
        cmd += " --cov=src --cov-report=html --cov-report=term"

    ctx.run(cmd)

    if coverage:
        print("📊 Coverage report generated in htmlcov/")


@task
def test_unit(ctx):
    """Run only unit tests."""
    print("🧪 Running unit tests...")
    ctx.run("uv run pytest tests/ -v -m 'unit' --tb=short")


@task
def test_integration(ctx):
    """Run only integration tests."""
    print("🧪 Running integration tests...")
    ctx.run("uv run pytest tests/ -v -m 'integration' --tb=short")


@task
def start_infra(ctx):
    """Start infrastructure services with Docker Compose."""
    print("🐳 Starting infrastructure services...")

    # Check if Docker is running
    if not ctx.run("docker info", warn=True, hide=True).ok:
        print("❌ Docker is not running. Please start Docker first.")
        sys.exit(1)

    # Start services
    ctx.run("docker-compose up -d")

    print("⏳ Waiting for services to be ready...")
    ctx.run("docker-compose ps")

    print("✅ Infrastructure services started!")
    print("   - Neo4j Browser: http://localhost:7474")
    print("   - NATS Management: http://localhost:8222")
    print("   - Azurite Blob: http://localhost:10000")


@task
def stop_infra(ctx):
    """Stop infrastructure services."""
    print("🛑 Stopping infrastructure services...")
    ctx.run("docker-compose down")
    print("✅ Infrastructure services stopped!")


@task
def restart_infra(ctx):
    """Restart infrastructure services."""
    print("🔄 Restarting infrastructure services...")
    ctx.run("docker-compose restart")
    print("✅ Infrastructure services restarted!")


@task
def logs_infra(ctx, service=""):
    """Show logs for infrastructure services."""
    if service:
        print(f"📜 Showing logs for {service}...")
        ctx.run(f"docker-compose logs -f {service}")
    else:
        print("📜 Showing logs for all services...")
        ctx.run("docker-compose logs -f")


@task
def clean(ctx):
    """Clean up build artifacts and caches."""
    print("🧹 Cleaning up...")

    # Remove Python cache files
    ctx.run("find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true")
    ctx.run("find . -type f -name '*.pyc' -delete 2>/dev/null || true")

    # Remove test artifacts
    ctx.run("rm -rf .pytest_cache htmlcov .coverage")

    # Remove mypy cache
    ctx.run("rm -rf .mypy_cache")

    print("✅ Cleanup complete!")


@task
def check(ctx):
    """Run all quality checks (lint + test)."""
    print("🔍 Running comprehensive checks...")
    lint(ctx)
    test(ctx)
    print("✅ All checks passed!")


@task
def scaffolding_info(ctx):
    """Show scaffolding configuration information."""
    print("ℹ️  Running scaffolding info...")
    ctx.run("uv run python -m src.scaffolding.cli info")


@task
def scaffolding_check(ctx):
    """Run scaffolding health checks."""
    print("🏥 Running scaffolding health checks...")
    ctx.run("uv run python -m src.scaffolding.cli check")


@task
def create_env_template(ctx):
    """Create .env.template file."""
    print("📝 Creating .env.template...")
    ctx.run("uv run python -c \"from src.scaffolding.config import create_env_template; create_env_template()\"")
    print("✅ .env.template created!")
