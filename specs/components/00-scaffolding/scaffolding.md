# Project Scaffolding Specification

## 1. Purpose / Overview

The Project Scaffolding component provides **unified cross-cutting infrastructure** that establishes foundational tooling, development workflows, and repository structure for the entire SimBuilder ecosystem. This component ensures consistent development practices, automated quality gates, and streamlined onboarding across all other components.

**Core Purpose:** Unify cross-cutting infrastructure including uv package management, pyproject.toml configuration, Ruff linting, Black formatting, pre-commit hooks, pytest configuration, .env handling, prompts folder organization, and Docker dev-container setup.

### 1.1 Key Capabilities
- **Bootstrap CLI Command:** `sim init` for rapid project initialization
- **Unified Python Tooling:** uv, pyproject.toml, Ruff, Black, pytest integration
- **Development Environment:** Docker dev-container with all required tools
- **Quality Gates:** Pre-commit hooks, automated linting, testing pipelines
- **Configuration Management:** Centralized .env handling and config schemas
- **Documentation Templates:** CONTRIBUTING.md, CODEOWNERS, ADR templates

## 2. Functional Requirements / User Stories

### 2.1 Contributors (New Team Members)
- **US-001:** As a new contributor, I want to run `sim init` and have a fully configured development environment within 5 minutes
- **US-002:** As a developer, I want consistent code formatting and linting across all components without manual configuration
- **US-003:** As a contributor, I want pre-commit hooks to catch issues before they reach CI/CD

### 2.2 CI/CD System 
- **US-004:** As a CI system, I want standardized Make targets (`make test`, `make lint`, `make build`) that work consistently across all components
- **US-005:** As a build system, I want lockfile-based dependency management for reproducible builds

### 2.3 Security Team
- **US-006:** As a security engineer, I want centralized secret management with .env templates and validation
- **US-007:** As a compliance officer, I want CODEOWNERS enforcement and signed commits for audit trails

### 2.4 DevOps Team
- **US-008:** As a platform engineer, I want containerized development environments that match production closely

## 3. Interfaces / APIs

### 3.1 CLI Bootstrap Interface
```bash
# Primary bootstrap command
sim init [--template=python|node|full] [--path=./project]

# Component-specific initialization
sim init component --name=my-agent --type=agent

# Update existing project scaffolding
sim scaffold update
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

### 3.3 Dev-Container Configuration
```json
{
  "name": "SimBuilder Dev Environment",
  "dockerFile": "../docker/dev.Dockerfile",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python", "charliermarsh.ruff"],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python"
      }
    }
  }
}
```

### 3.4 Messaging & Local Broker
SimBuilder uses NATS JetStream for local development messaging, with environment variable switching to Azure Service Bus for production.

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
# .env.example - Local development
SIMBUS_BACKEND=nats
NATS_URL=nats://localhost:4222

# .env.production - Azure production
SIMBUS_BACKEND=azure_service_bus
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...
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
│   └── prod.Dockerfile
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
├── pyproject.toml
├── Makefile
├── .env.example
├── .pre-commit-config.yaml
└── uv.lock
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
- **Multi-language monorepo vs polyrepo:** Should Python and Node.js components share a repository or be separated?
- **Component isolation:** How granular should component separation be for independent development?

### 9.2 Dependency Management
- **Lockfile strategy:** Should we use uv.lock at the root level or per-component lockfiles?
- **Version synchronization:** How do we keep shared dependencies in sync across components?

### 9.3 Development Environment
- **Docker vs Nix:** Should we standardize on Docker dev-containers or explore Nix for reproducible environments?
- **Tool versions:** How do we handle different team members wanting different tool versions?

### 9.4 CI/CD Integration
- **Monorepo CI:** How do we optimize CI runs to only test affected components in a monorepo?
- **Secret management:** What approach for managing secrets across development and production environments?

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