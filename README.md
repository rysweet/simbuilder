# SimBuilder Scaffolding Package

A foundational Python package that provides shared utilities, configuration management, and
infrastructure components for the SimBuilder Azure tenant discovery and simulation platform.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker (for running infrastructure services)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd simbuilder
   ```

1. **Bootstrap the development environment:**

   ```bash
   uv venv .venv --python 3.12
   uv pip install -r requirements.txt
   ```

   Or use the provided tasks:

   ```bash
   python tasks.py bootstrap
   ```

1. **Configure environment:**

   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

1. **Create a new session and start infrastructure services:**

   ```bash
   # Install the package in development mode
   pip install -e .

   # Create a new session with dynamic ports and start containers
   simbuilder session create --start-containers
   ```

## 📦 Package Structure

```
src/scaffolding/
├── __init__.py          # Package exports
├── config.py            # Pydantic settings management
├── exceptions.py        # Custom exception types
├── logging.py           # Structured logging setup
└── cli.py              # Command-line interface
```

## 🔧 Configuration

The scaffolding package uses Pydantic Settings for configuration management with automatic
environment variable loading.

### Required Configuration

```bash
# Azure Authentication
AZURE_TENANT_ID=your-tenant-id
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key

# Database
NEO4J_PASSWORD=your-secure-password
```

### Optional Configuration

```bash
# Service endpoints
NEO4J_URI=neo4j://localhost:7687
SERVICE_BUS_URL=nats://localhost:4222
CORE_API_URL=http://localhost:7000

# Application settings
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG_MODE=true
```

## 🛠️ CLI Usage

The scaffolding package provides a CLI for system administration, session management, and health
checks:

### Session Management

Create a new session with dynamic port allocation:

```bash
# Create session only
simbuilder session create

# Create session and start containers
simbuilder session create --start-containers

# Create session with specific services
simbuilder session create --services "neo4j,nats,core_api"

# Create session with Docker Compose profile
simbuilder session create --start-containers --profile full
```

List existing sessions:

```bash
simbuilder session list
```

Check session status:

```bash
simbuilder session status <session-id>
```

Clean up a session:

```bash
simbuilder session cleanup <session-id>
```

### View Configuration

```bash
simbuilder info
```

### Health Checks

```bash
simbuilder check
```

## 🏗️ Infrastructure Services

### Session-Aware Infrastructure

SimBuilder uses a session-aware approach to infrastructure management with dynamic port allocation
to avoid conflicts:

1. **Create a session**: Generates unique ports and container names
1. **Environment variables**: All configuration stored in `.env.session`
1. **Docker Compose**: Uses environment variables for ports and project naming

### Start Services with Session

```bash
# Create session and start services
simbuilder session create --start-containers

# Or manually start services for existing session
docker compose -p simbuilder-<session-short> --env-file .env.session up -d
```

The compose file includes:

- **Neo4j** - Graph database with dynamic ports
- **NATS** - Message bus with JetStream and dynamic ports
- **Azurite** - Azure Storage emulator with dynamic ports
- **Core API** - Placeholder service (profile: full)
- **API Gateway** - Placeholder service (profile: full)

### Stop Services

```bash
# Using session management
simbuilder session cleanup <session-id>

# Or manually
docker compose -p simbuilder-<session-short> --env-file .env.session down
```

### Environment Variables

After creating a session, `.env.session` contains:

```bash
SIMBUILDER_SESSION_ID=uuid-v4-session-id
COMPOSE_PROJECT_NAME=simbuilder-<8-char-short-id>
NEO4J_PORT=30002
NEO4J_HTTP_PORT=30003
NATS_PORT=30004
NATS_HTTP_PORT=30005
# ... other dynamic ports
```

## 🧪 Development

### Code Quality

The project uses modern Python tooling:

- **Ruff** - Fast Python linter and formatter
- **MyPy** - Static type checking
- **Pytest** - Testing framework
- **Pre-commit** - Git hooks for quality checks

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src

# Unit tests only
uv run pytest -m unit
```

### Linting and Formatting

```bash
# Check code quality
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Type checking
uv run mypy src/
```

### Project Tasks

Common development tasks are automated in `tasks.py`:

```bash
# Bootstrap environment
python tasks.py bootstrap

# Run linting
python tasks.py lint

# Format code
python tasks.py format

# Run tests
python tasks.py test

# Start infrastructure
python tasks.py start-infra

# Health checks
python tasks.py scaffolding-check
```

## 📊 Package Features

### Configuration Management

- Type-safe Pydantic settings
- Environment variable loading
- Validation and error handling
- Development/production modes

### Structured Logging

- JSON output for production
- Pretty console output for development
- Contextual logging with metadata
- Configurable log levels

### Error Handling

- Custom exception hierarchy
- Detailed error context
- Service availability checking

### CLI Interface

- Rich terminal output
- Health monitoring
- Configuration inspection
- Service diagnostics

## 🔌 Integration

### Using in Other Components

```python
from src.scaffolding import get_settings, setup_logging
from src.scaffolding.exceptions import ConfigurationError

# Initialize logging
logger = setup_logging()

# Load configuration
try:
    settings = get_settings()
    logger.info("Configuration loaded", environment=settings.environment)
except ConfigurationError as e:
    logger.error("Configuration failed", error=str(e))
```

### Custom Components

```python
from src.scaffolding.logging import LoggingMixin
from src.scaffolding.config import get_settings


class MyService(LoggingMixin):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()

    def process_data(self, data):
        self.log_method_call("process_data", data_size=len(data))
        try:
            # Process data
            pass
        except Exception as e:
            self.log_error(e, {"operation": "process_data"})
            raise
```

## 🏛️ Architecture

The scaffolding package follows these design principles:

- **Configuration as Code** - All settings in version control
- **Fail Fast** - Early validation of configuration and dependencies
- **Observable** - Comprehensive logging and health checking
- **Testable** - Unit tests with mocking for external dependencies
- **Portable** - Works across development, staging, and production

## 📋 Requirements

### Runtime Dependencies

- `pydantic>=2.5.0` - Data validation and settings
- `structlog>=23.2.0` - Structured logging
- `typer>=0.9.0` - CLI framework
- `rich>=13.7.0` - Terminal formatting
- `neo4j>=5.15.0` - Graph database client
- `nats-py>=2.6.0` - NATS message bus client

### Development Dependencies

- `pytest>=7.4.0` - Testing framework
- `ruff>=0.1.6` - Linting and formatting
- `mypy>=1.7.0` - Type checking
- `pre-commit>=3.5.0` - Git hooks

## 🤝 Contributing

1. Install development dependencies: `python tasks.py bootstrap`
1. Install pre-commit hooks: `pre-commit install`
1. Run tests: `python tasks.py test`
1. Check code quality: `python tasks.py lint`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ☁️ GitHub Codespaces & Dev Containers

SimBuilder includes full support for GitHub Codespaces and VS Code Dev Containers with
Docker-in-Docker capability.

### Using GitHub Codespaces

1. **Open in Codespaces**: Click "Code" → "Codespaces" → "Create codespace"
1. **Automatic Setup**: The devcontainer will automatically:
   - Install Python dependencies
   - Create a new session
   - Start Docker Compose services
   - Forward necessary ports

### Using VS Code Dev Containers

1. **Open in VS Code**: Install the "Dev Containers" extension
1. **Reopen in Container**: Command palette → "Dev Containers: Reopen in Container"
1. **Automatic Setup**: Same as Codespaces

### Port Forwarding

The devcontainer automatically forwards these ports:

- **7474**: Neo4j Browser (HTTP interface)
- **7687**: Neo4j Bolt protocol
- **4222**: NATS messaging
- **8222**: NATS management interface
- **10000**: Azurite blob storage
- **8080**: Core API service
- **8090**: API Gateway

### Manual Commands in Codespaces

If you need to recreate the session:

```bash
# Create new session and start containers
simbuilder session create --start-containers

# Or just create session without starting containers
simbuilder session create
```

## 🔗 Related Documentation

- [SimBuilder Overview](specs/SimBuilderOverview.md)
- [Component Specifications](specs/components/)
- [API Documentation](docs/api/)
