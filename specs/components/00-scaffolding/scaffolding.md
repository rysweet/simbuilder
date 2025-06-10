# Project Scaffolding Specification

## 1. Purpose / Overview

The Project Scaffolding component provides **unified cross-cutting infrastructure** that establishes
foundational tooling, development workflows, and repository structure for the entire SimBuilder
ecosystem. This component ensures consistent development practices, automated quality gates, and
streamlined onboarding across all other components.

**Core Purpose:** Unify cross-cutting infrastructure including uv package management, pyproject.toml
configuration, Ruff linting, Black formatting, pre-commit hooks, pytest configuration, .env
handling, prompts folder organization, Docker dev-container setup, session management, and dynamic
port allocation for multi-instance support.

### 1.1 Key Capabilities

- **Bootstrap CLI Command:** `sim init` for rapid project initialization
- **Session Management:** Global session ID generation and isolation
- **Dynamic Port Allocation:** Runtime port scanning and conflict-free assignment
- **Multi-Instance Support:** Concurrent execution with resource isolation
- **Unified Python Tooling:** uv, pyproject.toml, Ruff, Black, pytest integration
- **Development Environment:** Docker dev-container with all required tools
- **Quality Gates:** Pre-commit hooks, automated linting, testing pipelines
- **Configuration Management:** Centralized .env handling and config schemas
- **Documentation Templates:** CONTRIBUTING.md, CODEOWNERS, ADR templates

## 2. Functional Requirements / User Stories

### 2.1 Session Management and Multi-Instance Support

- **US-001:** As a developer, I want to run multiple SimBuilder instances simultaneously without
  port conflicts
- **US-002:** As a CI/CD system, I want each pipeline run to have isolated resources and not
  interfere with others
- **US-003:** As a GitHub Codespaces user, I want SimBuilder to work seamlessly in containerized
  environments
- **US-004:** As a team member, I want session cleanup to happen automatically when I stop working
- **US-005:** As a developer, I want to easily identify which containers belong to my session

### 2.2 Contributors (New Team Members)

- **US-006:** As a new contributor, I want to run `sim init` and have a fully configured development
  environment within 5 minutes
- **US-007:** As a developer, I want consistent code formatting and linting across all components
  without manual configuration
- **US-008:** As a contributor, I want pre-commit hooks to catch issues before they reach CI/CD

### 2.3 CI/CD System

- **US-009:** As a CI system, I want standardized Make targets (`make test`, `make lint`,
  `make build`) that work consistently across all components
- **US-010:** As a build system, I want lockfile-based dependency management for reproducible builds

### 2.4 Security Team

- **US-011:** As a security engineer, I want centralized secret management with .env templates and
  validation
- **US-012:** As a compliance officer, I want CODEOWNERS enforcement and signed commits for audit
  trails

### 2.5 DevOps Team

- **US-013:** As a platform engineer, I want containerized development environments that match
  production closely

## 3. Interfaces / APIs

### 3.1 CLI Bootstrap Interface

```bash
# Primary bootstrap command with session management
sim init [--template=python|node|full] [--path=./project] [--session-id=UUID]

# Component-specific initialization
sim init component --name=my-agent --type=agent

# Update existing project scaffolding
sim scaffold update

# Session management commands
sim session create [--ports=custom-range]
sim session list
sim session cleanup [--session-id=UUID]
sim session status [--session-id=UUID]
```

### 3.2 Session ID Handling

```bash
# Session ID generation and management
sim session create
# Output: Created session a1b2c3d4-e5f6-7890-abcd-ef1234567890
#         Allocated ports: Neo4j=17474,17687 NATS=14222 API=18080

# Environment variable setup
sim session env [--session-id=UUID]
# Output: Environment variables for session a1b2c3d4:
#         SIMBUILDER_SESSION_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
#         COMPOSE_PROJECT_NAME=simbuilder-a1b2c3d4
#         GRAPH_DB_HTTP_PORT=17474
#         GRAPH_DB_BOLT_PORT=17687

# Session cleanup
sim session cleanup --session-id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
# Output: Stopped containers: simbuilder-neo4j-a1b2c3d4, simbuilder-nats-a1b2c3d4
#         Removed networks: simbuilder-a1b2c3d4-network
#         Released ports: 17474, 17687, 14222, 18080
```

### 3.3 Dynamic Port Allocation

```python
# Port allocation interface
class PortManager:
    def allocate_ports(self, service_configs: dict) -> dict:
        """Allocate available ports for services"""

    def release_ports(self, session_id: str) -> bool:
        """Release ports allocated to a session"""

    def get_port_ranges(self) -> dict:
        """Get configured port ranges for each service type"""

    def check_conflicts(self, ports: list) -> list:
        """Check for port conflicts with existing sessions"""
```

### 3.2 Make Targets (Standardized across all components)

```makefile
make install     # Install dependencies with uv
make proto       # Compile /proto/*.proto to Python bindings
make dev         # Start development environment
make test        # Run all tests with pytest
make lint        # Run Ruff linting
make format      # Run Black formatting
make check       # Run all quality checks
make build       # Build Docker images
make clean       # Clean build artifacts
```

#### Proto Compilation Integration

```makefile
# Makefile excerpt for /proto compilation
.PHONY: proto
proto:
	@echo "Compiling protobuf schemas..."
	protoc --python_out=src/shared/messages \
	       --proto_path=proto \
	       proto/*.proto
	@echo "Generated Python bindings in src/shared/messages/"

# uv build hook integration
install: proto
	uv pip install -e .
```

### 3.4 Dev-Container Configuration with Docker-in-Docker Support

```json
{
  "name": "SimBuilder Dev Environment",
  "dockerFile": "../docker/dev.Dockerfile",
  "mounts": [
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
  ],
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/docker-outside-of-docker:1": {}
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff",
        "ms-azuretools.vscode-docker",
        "ms-vscode-remote.remote-containers"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "docker.dockerPath": "/usr/local/bin/docker"
      }
    }
  },
  "forwardPorts": [
    "17474", "17687", "14222", "18080"
  ],
  "portsAttributes": {
    "17474": {
      "label": "Neo4j Browser",
      "onAutoForward": "openPreview"
    },
    "17687": {
      "label": "Neo4j Bolt Protocol"
    },
    "14222": {
      "label": "NATS Client"
    },
    "18080": {
      "label": "API Gateway",
      "onAutoForward": "openPreview"
    }
  },
  "postCreateCommand": "sim session create && sim init",
  "shutdownAction": "stopCompose"
}
```

### 3.5 GitHub Codespaces Integration

```yaml
# .devcontainer/devcontainer.json for Codespaces
{
  "name": "SimBuilder Codespaces",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {
      "version": "latest",
      "enableNonRootDocker": "true"
    },
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "customizations": {
    "codespaces": {
      "openFiles": [
        "README.md",
        "specs/SimBuilderDesign.md"
      ]
    }
  },
  "postCreateCommand": ".devcontainer/postCreate.sh",
  "forwardPorts": [
    17474, 17687, 14222, 18080
  ],
  "portsAttributes": {
    "17474": {
      "label": "Neo4j Browser",
      "visibility": "public"
    },
    "18080": {
      "label": "SimBuilder API",
      "visibility": "public"
    }
  }
}
```

### 3.4 Messaging & Local Broker

SimBuilder uses NATS JetStream for local development messaging, with environment variable switching
to Azure Service Bus for production.

#### Docker-compose NATS Configuration

```yaml
# docker/dev-compose.yml
version: '3.8'
services:
  nats:
    image: nats:2.10-alpine
    ports:
      - "4222:4222"
      - "8222:8222"
    command: ["--jetstream", "--store_dir=/data"]
    volumes:
      - nats_data:/data
    environment:
      - NATS_LOG_LEVEL=info

volumes:
  nats_data:
```

#### Environment Variable Configuration

```bash
# .env.example - Local development with session isolation
SIMBUS_BACKEND=nats
NATS_URL=nats://localhost:${NATS_CLIENT_PORT}

# Session-specific configuration
SIMBUILDER_SESSION_ID=${SESSION_ID}
COMPOSE_PROJECT_NAME=simbuilder-${SESSION_ID_SHORT}

# Dynamic port allocation
GRAPH_DB_HTTP_PORT=${ALLOCATED_NEO4J_HTTP_PORT}
GRAPH_DB_BOLT_PORT=${ALLOCATED_NEO4J_BOLT_PORT}
NATS_CLIENT_PORT=${ALLOCATED_NATS_CLIENT_PORT}
NATS_HTTP_PORT=${ALLOCATED_NATS_HTTP_PORT}
API_GATEWAY_PORT=${ALLOCATED_API_GATEWAY_PORT}
AZURITE_BLOB_PORT=${ALLOCATED_AZURITE_BLOB_PORT}
AZURITE_QUEUE_PORT=${ALLOCATED_AZURITE_QUEUE_PORT}
AZURITE_TABLE_PORT=${ALLOCATED_AZURITE_TABLE_PORT}

# .env.production - Azure production
SIMBUS_BACKEND=azure_service_bus
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...
```

#### Session Environment File (.env.session)

```bash
# Generated automatically by scaffolding layer
SIMBUILDER_SESSION_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
COMPOSE_PROJECT_NAME=simbuilder-a1b2c3d4
SESSION_ID_SHORT=a1b2c3d4
SESSION_CREATED_AT=2025-06-06T14:30:00Z

# Allocated ports for this session
GRAPH_DB_HTTP_PORT=17474
GRAPH_DB_BOLT_PORT=17687
NATS_CLIENT_PORT=14222
NATS_HTTP_PORT=18222
API_GATEWAY_PORT=18080
AZURITE_BLOB_PORT=11000
AZURITE_QUEUE_PORT=11001
AZURITE_TABLE_PORT=11002

# Connection strings using allocated ports
NEO4J_URI=bolt://localhost:17687
NEO4J_HTTP_URI=http://localhost:17474
NATS_URL=nats://localhost:14222
AZURITE_BLOB_URI=http://localhost:11000
AZURITE_QUEUE_URI=http://localhost:11001
AZURITE_TABLE_URI=http://localhost:11002
```

## 4. Dependencies

### 4.1 Runtime Dependencies

- **Python 3.12+** - Primary language runtime
- **Node.js 18+** - Frontend tooling and UI components
- **Docker Desktop** - Containerization and dev-containers
- **Git** - Version control and collaboration

### 4.2 Cloud Infrastructure Dependencies

- **Azure CLI** - Azure resource management
- **Terraform CLI 1.5+** - Infrastructure as Code
- **Azure Kubernetes Service (AKS)** - Container orchestration
- **Azure Container Registry** - Container image storage

### 4.3 Development Tool Dependencies

- **uv** - Fast Python package management
- **Ruff** - Python linting and formatting
- **Black** - Code formatting
- **pytest** - Testing framework
- **pre-commit** - Git hook management

### 4.4 Component Repository Dependencies

All component repositories must conform to the scaffolding structure:

- [`01-graph-database-service`](../01-graph-database-service/graph-database-service.md)
- [`02-service-bus`](../02-service-bus/service-bus.md)
- [`03-spec-library`](../03-spec-library/spec-library.md)
- [`04-core-api-service`](../04-core-api-service/core-api-service.md)
- All agent components (05-23)

## 5. Data Contracts

### 5.1 Repository Directory Layout

```
simbuilder/
├── .devcontainer/
│   ├── devcontainer.json
│   └── docker/
├── .github/
│   ├── workflows/
│   ├── CODEOWNERS
│   └── ISSUE_TEMPLATE/
├── docker/
│   ├── dev.Dockerfile
│   ├── prod.Dockerfile
│   └── docker-compose.session.yml.template
├── prompts/
│   ├── agents/
│   └── shared/
├── src/
│   ├── shared/
│   └── components/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── acceptance/
├── docs/
│   ├── CONTRIBUTING.md
│   └── adr/
├── sessions/
│   ├── .gitkeep
│   └── active_sessions.json
├── pyproject.toml
├── Makefile
├── .env.example
├── .env.session
├── .pre-commit-config.yaml
└── uv.lock
```

### 5.2 Session Management Data Structures

#### Session Registry Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "activeSessions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sessionId": {
            "type": "string",
            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
          },
          "sessionIdShort": {
            "type": "string",
            "pattern": "^[0-9a-f]{8}$"
          },
          "createdAt": {
            "type": "string",
            "format": "date-time"
          },
          "lastActivity": {
            "type": "string",
            "format": "date-time"
          },
          "allocatedPorts": {
            "type": "object",
            "properties": {
              "neo4jHttp": {"type": "integer"},
              "neo4jBolt": {"type": "integer"},
              "natsClient": {"type": "integer"},
              "natsHttp": {"type": "integer"},
              "apiGateway": {"type": "integer"},
              "azuriteBlob": {"type": "integer"},
              "azuriteQueue": {"type": "integer"},
              "azuriteTable": {"type": "integer"}
            },
            "required": ["neo4jHttp", "neo4jBolt", "natsClient"]
          },
          "containerNames": {
            "type": "array",
            "items": {"type": "string"}
          },
          "networkName": {"type": "string"},
          "status": {
            "type": "string",
            "enum": ["active", "stopped", "cleanup_pending"]
          }
        },
        "required": ["sessionId", "sessionIdShort", "createdAt", "allocatedPorts", "status"]
      }
    }
  },
  "required": ["activeSessions"]
}
```

#### Port Allocation Configuration

```yaml
# Port allocation configuration
portRanges:
  neo4j:
    http:
      min: 17000
      max: 17999
    bolt:
      min: 17000
      max: 17999
  nats:
    client:
      min: 14000
      max: 14999
    http:
      min: 14000
      max: 14999
  api:
    gateway:
      min: 18000
      max: 18999
  azurite:
    blob:
      min: 11000
      max: 11999
    queue:
      min: 11000
      max: 11999
    table:
      min: 11000
      max: 11999

# Port allocation strategy
allocationStrategy:
  conflictResolution: "increment_and_retry"
  maxRetries: 100
  reservationTimeout: 30 # seconds
  cleanupInterval: 300 # seconds
```

### 5.3 Session-Aware Docker Compose Template

#### docker-compose.session.yml.template

```yaml
# Session-isolated docker-compose template
# Variables are substituted by scaffolding layer
version: '3.8'

services:
  neo4j:
    image: neo4j:5.11
    container_name: ${COMPOSE_PROJECT_NAME}-neo4j
    ports:
      - "${GRAPH_DB_HTTP_PORT}:7474"
      - "${GRAPH_DB_BOLT_PORT}:7687"
    environment:
      - NEO4J_AUTH=neo4j/your-secure-password
      - NEO4J_apoc_export_file_enabled=true
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
      - NEO4J_dbms_default_database=simbuilder
    volumes:
      - neo4j_data_${SESSION_ID_SHORT}:/data
      - neo4j_logs_${SESSION_ID_SHORT}:/logs
      - neo4j_import_${SESSION_ID_SHORT}:/var/lib/neo4j/import
      - neo4j_plugins_${SESSION_ID_SHORT}:/plugins
    networks:
      - ${COMPOSE_PROJECT_NAME}-network
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "your-secure-password", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  nats:
    image: nats:2.10-alpine
    container_name: ${COMPOSE_PROJECT_NAME}-nats
    ports:
      - "${NATS_CLIENT_PORT}:4222"
      - "${NATS_HTTP_PORT}:8222"
      - "6222:6222"
    command: [
      "--jetstream",
      "--store_dir=/data",
      "--http_port=8222",
      "--cluster_name=${COMPOSE_PROJECT_NAME}-cluster"
    ]
    volumes:
      - nats_data_${SESSION_ID_SHORT}:/data
    networks:
      - ${COMPOSE_PROJECT_NAME}-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8222/varz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  azurite:
    image: mcr.microsoft.com/azure-storage/azurite:latest
    container_name: ${COMPOSE_PROJECT_NAME}-azurite
    ports:
      - "${AZURITE_BLOB_PORT}:10000"
      - "${AZURITE_QUEUE_PORT}:10001"
      - "${AZURITE_TABLE_PORT}:10002"
    volumes:
      - azurite_data_${SESSION_ID_SHORT}:/data
    networks:
      - ${COMPOSE_PROJECT_NAME}-network
    command: >
      azurite
      --blobHost 0.0.0.0
      --queueHost 0.0.0.0
      --tableHost 0.0.0.0
      --location /data
      --debug /data/debug.log
    healthcheck:
      test: ["CMD", "nc", "-z", "localhost", "10000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  neo4j_data_${SESSION_ID_SHORT}:
    driver: local
  neo4j_logs_${SESSION_ID_SHORT}:
    driver: local
  neo4j_import_${SESSION_ID_SHORT}:
    driver: local
  neo4j_plugins_${SESSION_ID_SHORT}:
    driver: local
  nats_data_${SESSION_ID_SHORT}:
    driver: local
  azurite_data_${SESSION_ID_SHORT}:
    driver: local

networks:
  ${COMPOSE_PROJECT_NAME}-network:
    driver: bridge
    name: ${COMPOSE_PROJECT_NAME}-network
```

### 5.2 Configuration File Schemas

#### pyproject.toml Structure

```toml
[project]
name = "simbuilder"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pydantic>=2.4.0"
]

[tool.ruff]
target-version = "py312"
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
```

#### pytest.ini Configuration

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
addopts = --strict-markers --strict-config
markers =
    unit: Unit tests
    integration: Integration tests
    acceptance: End-to-end acceptance tests
```

#### .env.example Template

```bash
# Azure Configuration
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_SUBSCRIPTION_ID=

# OpenAI Configuration
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=

# Service Bus Configuration
AZURE_SERVICE_BUS_CONNECTION_STRING=
```

## 6. Documentation to Produce

### 6.1 Core Documentation Files

- **CONTRIBUTING.md** - Development workflow, coding standards, PR process
- **CODEOWNERS** - Component ownership and review assignments
- **README.md** - Project overview and quick start guide
- **.github/ISSUE_TEMPLATE/** - Bug report and feature request templates

### 6.2 Architecture Decision Records (ADRs)

- **ADR-001:** Python tooling standardization (uv vs pip/poetry)
- **ADR-002:** Linting strategy (Ruff vs pylint/flake8)
- **ADR-003:** Container strategy (Docker vs Nix)
- **ADR-004:** Monorepo vs polyrepo structure

### 6.3 Dev-Container Documentation

- **Dev Environment Setup Guide** - VSCode dev-container configuration
- **Tool Integration Guide** - Ruff, Black, pytest VSCode integration
- **Troubleshooting Guide** - Common dev-container issues and solutions

## 7. Testing Strategy

### 7.1 Scaffold Self-Test Approach

Create a temporary test project and validate full scaffolding functionality:

```python
def test_scaffold_complete_workflow():
    """Test complete scaffolding workflow with temporary project."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize new project
        result = subprocess.run(["sim", "init", "--path", temp_dir])
        assert result.returncode == 0

        # Validate directory structure
        assert_directory_structure(temp_dir)

        # Test development workflow
        assert_make_targets_work(temp_dir)

        # Test quality gates
        assert_linting_passes(temp_dir)
        assert_tests_pass(temp_dir)

        # Test dev-container
        assert_devcontainer_builds(temp_dir)
```

### 7.2 Test Categories

- **Unit Tests:** Individual scaffold generation functions
- **Integration Tests:** End-to-end project initialization workflows
- **Acceptance Tests:** Real development environment validation

### 7.3 Quality Validation Tests

- **Linting Tests:** Ensure all generated code passes Ruff checks
- **Format Tests:** Verify Black formatting compliance
- **Security Tests:** Validate .env template security practices
- **Documentation Tests:** Check all required documentation is generated

## 8. Acceptance Criteria

### 8.1 Quality Gates

- ✅ **All linting passes:** Ruff reports zero violations on generated code
- ✅ **Installation works:** `uv pip install .` succeeds in clean environment
- ✅ **Tests pass:** `pytest` runs green with 100% success rate
- ✅ **Dev-container builds:** VSCode dev-container spins up without errors

### 8.2 Functional Requirements

- ✅ **Bootstrap speed:** `sim init` completes in under 60 seconds
- ✅ **Dependency resolution:** uv resolves all dependencies consistently
- ✅ **Cross-platform:** Works on Windows, macOS, and Linux
- ✅ **VSCode integration:** All dev tools work seamlessly in VSCode

### 8.3 Documentation Requirements

- ✅ **CONTRIBUTING.md:** Complete development workflow documentation
- ✅ **CODEOWNERS:** All components have designated owners
- ✅ **ADRs:** Key architectural decisions are documented
- ✅ **API Documentation:** All CLI commands have help text and examples

## 9. Open Questions

### 9.1 Repository Structure

- **Multi-language monorepo vs polyrepo:** Should Python and Node.js components share a repository
  or be separated?
- **Component isolation:** How granular should component separation be for independent development?

### 9.2 Dependency Management

- **Lockfile strategy:** Should we use uv.lock at the root level or per-component lockfiles?
- **Version synchronization:** How do we keep shared dependencies in sync across components?

### 9.3 Development Environment

- **Docker vs Nix:** Should we standardize on Docker dev-containers or explore Nix for reproducible
  environments?
- **Tool versions:** How do we handle different team members wanting different tool versions?

### 9.4 CI/CD Integration

- **Monorepo CI:** How do we optimize CI runs to only test affected components in a monorepo?
- **Secret management:** What approach for managing secrets across development and production
  environments?

### 9.5 Documentation Strategy

- **Documentation generation:** Should we auto-generate API docs from code or maintain manually?
- **ADR workflow:** What process for proposing, reviewing, and approving architectural decisions?

## 10. Implementation Roadmap

### Phase 1: Core Scaffolding (Week 1)

- [ ] Create `sim init` CLI command
- [ ] Implement basic directory structure generation
- [ ] Set up pyproject.toml templates
- [ ] Configure Ruff and Black

### Phase 2: Development Workflow (Week 2)

- [ ] Implement Make targets
- [ ] Set up pre-commit hooks
- [ ] Create dev-container configuration
- [ ] Add pytest configuration

### Phase 3: Documentation & Polish (Week 3)

- [ ] Generate CONTRIBUTING.md template
- [ ] Create CODEOWNERS template
- [ ] Write ADR templates
- [ ] Add comprehensive testing

### Phase 4: Validation & Rollout (Week 4)

- [ ] Test scaffold with all existing components
- [ ] Validate dev-container across platforms
- [ ] Document troubleshooting guides
- [ ] Train team on new workflow
