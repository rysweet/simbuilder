# Tenant Discovery MVP – Implementation Plan

A focused MVP implementation prioritizing the Tenant Discovery Agent with essential supporting infrastructure to demonstrate comprehensive Azure tenant enumeration, graph database population, and narrative documentation generation capabilities.

## Scope / Components Included

### Core Services Required
- **Configuration Service** – Centralized configuration management and environment settings
- **Graph Database Service** – Neo4j with Docker Compose setup and connector libraries
- **Service Bus** – Azure Service Bus with local emulator for development
- **Spec Library** – Git repository management for baseline specifications
- **Core API Service** – CRUD operations, health endpoints, and session management
- **LLM Foundry Integration** – Basic text generation with Azure OpenAI authentication
- **Tenant Discovery Agent** – Complete enumeration logic with graph population and LLM integration

### Components Out of Scope
All other SimBuilder agents (Clarifier, Planner, InfraSynthesis, Orchestrator, DataSeeder, Validator), integration services (Microsoft Graph/Entra, Microsoft 365, Terraform/ARM runners, Sentinel, FinOps), user interfaces (CLI, GUI, MCP), and deployment orchestration beyond local development environment.

## Ordered Workstream Steps

| Phase | Goal | Key Tasks | Inputs | Outputs | Acceptance Criteria |
|-------|------|-----------|---------|---------|-------------------|
| **Phase 0** | **Repo Bootstrap** | • Create monorepo structure<br/>• Setup CI/CD pipeline<br/>• Configure development tooling<br/>• Create .env.template | Project requirements, tooling preferences | Monorepo structure, GitHub Actions, .env.template, README | CI pipeline passes, local development setup documented |
| **Phase 1** | **Configuration Service** | • Implement config loading/validation<br/>• Environment variable management<br/>• Service registration patterns<br/>• Unit tests (using `uv run`)<br/>• Self-contained integration tests | Configuration schemas, environment requirements | Configuration service library, tests, documentation | All unit tests pass, integration tests self-contained and passing, no test failures |
| **Phase 2** | **Graph Database Service** | • Docker Compose Neo4j setup<br/>• Connection management library<br/>• Schema definitions for Azure resources<br/>• Graph operations (CRUD, queries)<br/>• Unit tests before integration tests<br/>• Live Neo4j integration tests (no mocks) | Neo4j requirements, Azure resource schemas | Neo4j Docker setup, connector library, resource schema | Local Neo4j running, all tests passing with `uv run`, no disabled tests |
| **Phase 3** | **Service Bus** | • Azure Service Bus local emulator<br/>• Message publishing/consuming<br/>• Topic/subscription management<br/>• Error handling and retries<br/>• Self-contained integration tests<br/>• Live service bus testing (no mocks) | Service Bus requirements, message schemas | Service Bus connector, Docker setup, messaging patterns | Message flow working, all tests self-contained and passing |
| **Phase 4** | **Spec Library** | • Git repository integration<br/>• Specification loading/parsing<br/>• Version management<br/>• Baseline spec population<br/>• Unit and integration test suites | Specification formats, Git integration requirements | Spec library service, baseline specifications loaded | Specs loadable, version management functional, comprehensive test coverage |
| **Phase 5** | **Core API Service** | • FastAPI application setup<br/>• Session management endpoints<br/>• Health/status monitoring<br/>• Database integration<br/>• Authentication framework<br/>• API integration tests with live dependencies | API requirements, database schemas, auth patterns | FastAPI service, core endpoints, session management | All endpoints functional, session lifecycle working, API tests using real services |
| **Phase 6** | **LLM Foundry Integration** | • Azure OpenAI client setup<br/>• Authentication management<br/>• Basic text generation<br/>• Rate limiting and retries<br/>• Liquid template loading<br/>• Live Azure OpenAI integration tests | Azure OpenAI credentials, LLM requirements, template schemas | LLM service library, template engine, auth patterns | Text generation working, templates loading, live API integration verified |
| **Phase 7** | **Tenant Discovery Agent** | • Azure ARM/Resource Graph clients<br/>• Resource enumeration logic<br/>• Graph database population<br/>• LLM narrative generation<br/>• Rate limiting and error handling<br/>• End-to-end integration tests with live Azure APIs | Azure API documentation, discovery requirements, prompt templates | Complete Tenant Discovery Agent, Liquid templates | Full tenant discovery functional, comprehensive test coverage with live services |
| **Phase 8** | **Integration & E2E Tests** | • End-to-end discovery scenarios<br/>• Self-contained test environments<br/>• Live service integration validation<br/>• Error condition testing<br/>• Data consistency verification<br/>• Stop-on-first-failure testing workflow | Test scenarios, live service requirements | Test suite, validation reports, documented test procedures | All integration tests self-contained, pass independently, use live services |
| **Phase 9** | **Deployment** | • Docker Compose orchestration<br/>• Local environment scripts<br/>• Documentation updates<br/>• Deployment validation | Deployment requirements, documentation standards | Docker Compose files, bootstrap scripts, updated README | Local environment deployable with single command |
| **Phase 10** | **Production Readiness** | • Security hardening and threat modeling<br/>• Secret management and credential rotation<br/>• Monitoring and observability setup<br/>• Disaster recovery and backup procedures<br/>• Performance tuning and optimization<br/>• Compliance and audit requirements | Security requirements, operational standards | Security runbooks, monitoring dashboards, DR procedures | Security baseline established, production deployment ready |

## Dependencies / Order Rationale

The implementation order satisfies the dependency graph by ensuring foundational services are built before dependent components:

1. **Configuration Service** provides the foundation for all other services to load settings and manage environments
2. **Graph Database & Service Bus** establish core data storage and messaging infrastructure
3. **Spec Library** enables specification management required by agents
4. **Core API Service** builds on all infrastructure services to provide session management and coordination
5. **LLM Foundry Integration** provides AI capabilities needed by the Tenant Discovery Agent
6. **Tenant Discovery Agent** represents the culmination, depending on all previous components
7. **Integration Testing** validates the complete system functionality
8. **Deployment** packages everything for easy local development setup

## Dependencies

- CLI Interface (basic implementation) – used to initiate tenant discovery.
## Interface Overview

The following table summarizes the key interfaces between TenantDiscoveryMVP components:

| Provider Component | Consumer Component | Interface | Key Endpoints/Methods |
|-------------------|-------------------|-----------|----------------------|
| **Configuration Service** | All Components | Configuration API | `ConfigManager.get()`, `ConfigManager.get_section()` |
| **Graph Database Service** | Core API Service | REST API | `POST /graph/nodes`, `GET /graph/query` |
| **Graph Database Service** | Tenant Discovery Agent | Neo4j Connector | `Neo4jConnector.execute_query()`, `POST /tenant-discovery/import` |
| **Service Bus** | All Agents | CloudEvents Messaging | `ServiceBusClient.publish_message()`, `ServiceBusClient.subscribe_to_topic()` |
| **Core API Service** | CLI Interface | REST API | `POST /api/v1/simulations`, `GET /api/v1/simulations/{id}/status` |
| **Core API Service** | Tenant Discovery Agent | Session Management | `POST /api/v1/agents/register`, Agent coordination |
| **Spec Library** | Clarifier Agent | Template API | `GET /specs/templates/attacks`, `TemplateLibrary.search_templates()` |
| **Spec Library** | Planner Agent | Infrastructure Templates | `GET /specs/templates/infrastructure` |
| **LLM Foundry Integration** | Tenant Discovery Agent | LLM Client | `LLMClient.generate_text()`, Narrative generation |
| **LLM Foundry Integration** | CLI Interface | Interactive Assistance | `LLMClient.generate_chat_stream()` |
| **Tenant Discovery Agent** | Graph Database Service | Resource Import | `POST /tenant-discovery/import`, Azure resource graphs |
| **CLI Interface** | Configuration Service | Interactive Config | `ConfigurationPrompt.prompt_missing_config()` |

### Message Flow Patterns

1. **Discovery Workflow**: CLI → Core API → Tenant Discovery Agent → Graph Database Service
2. **Progress Updates**: Tenant Discovery Agent → Service Bus → Core API → CLI (real-time)
3. **Configuration Loading**: All Components → Configuration Service (startup)
4. **Template Access**: Agents → Spec Library → Git Repository (on-demand)
5. **Narrative Generation**: Tenant Discovery Agent → LLM Foundry Integration → Azure OpenAI
No circular dependencies exist in this design, enabling parallel development of infrastructure components (Phases 2-4) after Phase 1 completion.

## Deliverables

### Primary Deliverables
- **Working Local Environment**: Complete Docker Compose setup deployable via `bootstrap.sh` or `make up` commands
- **Tenant Discovery Capability**: Functional agent capable of full Azure tenant enumeration and graph population
- **CI/CD Pipeline**: Automated testing, linting, and validation workflows
- **Developer Documentation**: Setup guides, API documentation, and troubleshooting resources

### Technical Artifacts
- Monorepo structure with clear module separation
- Docker Compose orchestration for all services (Neo4j, Service Bus emulator, FastAPI, etc.)
- External Liquid template system for all LLM prompts (no hard-coded prompts)
- Comprehensive test suite (unit, integration, end-to-end) following strict testing requirements
- Configuration management supporting multiple environments
- Session-based discovery with progress tracking and error handling

## Testing & Validation Requirements

All implementation phases must adhere to strict testing and validation standards:

### Pre-Commit Standards
- All code must pass linting, formatting, unit tests, and integration tests before commit
- Always use `uv run` for test execution to ensure correct virtual environment
- Never skip, disable, or artificially pass tests

### Test Execution Workflow
- Run unit tests before integration tests in every phase
- Stop immediately on first test failure and fix before continuing
- Integration tests must be self-contained with their own setup/cleanup
- Integration tests must use live services (no mocks for components being tested)

For complete testing guidelines, see [.roo/rules-code/04-testing-requirements.md](../.roo/rules-code/04-testing-requirements.md).

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation Strategy |
|------|---------|-------------|-------------------|
| **LLM API Quota Limits** | High | Medium | • Implement aggressive caching<br/>• Rate limiting with exponential backoff<br/>• Fallback to simplified narrative generation |
| **Neo4j Licensing for Production** | Medium | Low | • Use Neo4j Community Edition for MVP<br/>• Document upgrade path to Enterprise<br/>• Consider alternative graph databases |
| **Service Bus Emulator Limitations** | Medium | Medium | • Validate core functionality locally<br/>• Document Azure Service Bus deployment<br/>• Implement feature flags for emulator vs cloud |
| **Azure API Rate Limiting** | High | High | • Conservative rate limiting (10 req/sec)<br/>• Exponential backoff with jitter<br/>• Batch operations where possible |
| **Complex Tenant Discovery Logic** | High | Medium | • Start with simple resource types<br/>• Iterative development approach<br/>• Extensive error handling and logging |
| **Liquid Template Complexity** | Medium | Medium | • Start with simple templates<br/>• Comprehensive template testing<br/>• Clear variable documentation |

## Next Steps Beyond MVP

### Immediate Extensions (Weeks 5-8)
- **Additional Agents**: Implement Clarifier and Planner agents to enable basic simulation workflow
- **CLI Interface**: Simple command-line interface for tenant discovery operations
- **Enhanced Narratives**: More sophisticated LLM-generated documentation with cost estimation
- **Incremental Discovery**: Change detection for previously discovered tenants

### Medium-term Roadmap (Months 2-3)
- **Full Agent Ecosystem**: Complete implementation of all SimBuilder agents
- **User Interfaces**: Web GUI and MCP service for broader accessibility
- **Cloud Deployment**: Kubernetes manifests and Azure deployment automation
- **Advanced Analytics**: Tenant comparison, security analysis, and compliance reporting

### Long-term Vision (Months 4-6)
- **Production Hardening**: Enterprise security, monitoring, and operational capabilities
- **Multi-tenant Support**: Concurrent discovery and management of multiple Azure tenants
- **Marketplace Integration**: Simulation templates and community-contributed scenarios
- **Advanced AI Features**: Intelligent simulation planning and automated optimization

## Local Development Environment

### Prerequisites

#### Required Software
- **Python 3.12**: Primary runtime for all services and agents
- **uv**: Modern Python package manager for dependency management and virtual environments
- **Docker Desktop**: Container runtime for Neo4j, NATS JetStream, and other infrastructure services
- **Azure CLI**: Required for tenant-scoped authentication and Azure resource discovery
- **Git**: Version control and repository management for spec library
- **Node.js 18+**: Optional, for any frontend development or JavaScript tooling

#### Azure Prerequisites
- **Azure Subscription**: Active subscription with resources for discovery testing
- **Azure Tenant Access**: Permissions to enumerate tenant resources via Azure Resource Graph
- **Service Principal** (Alternative): For automated authentication scenarios

### Environment Setup Steps

#### 1. Python Environment Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <repository-url>
cd simbuilder

# Create shared virtual environment at repo root
uv venv .venv --python 3.12

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
uv pip install -r requirements.txt
```

#### 2. Azure CLI Authentication
```bash
# Install Azure CLI (if not already installed)
# See: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Authenticate with tenant-scoped login
az login --tenant $AZURE_TENANT_ID

# Verify authentication and permissions
az account show
az graph query -q "Resources | limit 5"
```

#### 3. Infrastructure Services Setup
```bash
# Start local infrastructure via Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps

# Check service health
curl http://localhost:7474  # Neo4j Browser
curl http://localhost:8222  # NATS Management UI
```

#### 4. Configuration Setup
```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your specific values
# At minimum, update:
# - AZURE_TENANT_ID
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_KEY
# - NEO4J_PASSWORD
```

#### 5. Database Initialization
```bash
# Initialize Neo4j schema and constraints
uv run python -m simbuilder.graphdb.schema --initialize

# Verify database connectivity
uv run python -c "from simbuilder.graphdb import Neo4jConnector; Neo4jConnector().check_connection()"
```

#### 6. Service Bus Setup
```bash
# NATS JetStream should auto-configure via Docker Compose
# Verify message broker connectivity
uv run python -c "from simbuilder.servicebus import ServiceBusClient; print('Service Bus OK')"
```

### Environment Variables

All components share the same virtual environment located at `{repo_root}/.venv`. The following environment variables are required for local development:

| Variable | Description | Example Value | Required |
|----------|-------------|---------------|----------|
| **Azure Authentication** | | | |
| `AZURE_TENANT_ID` | Azure tenant identifier for authentication | `3cd87a41-1f61-4aef-a212-cefdecd9a2d1` | ✅ |
| `AZURE_CLIENT_ID` | Service principal client ID (if not using `az login`) | `app-registration-client-id` | ⚠️ |
| `AZURE_CLIENT_SECRET` | Service principal secret (if not using `az login`) | `your-client-secret` | ⚠️ |
| **Graph Database** | | | |
| `NEO4J_URI` | Neo4j connection string | `neo4j://localhost:7687` | ✅ |
| `NEO4J_USER` | Neo4j username | `neo4j` | ✅ |
| `NEO4J_PASSWORD` | Neo4j password | `your-secure-password` | ✅ |
| `NEO4J_DATABASE` | Neo4j database name | `simbuilder` | ✅ |
| **Service Bus** | | | |
| `SERVICE_BUS_URL` | NATS JetStream connection | `nats://localhost:4222` | ✅ |
| `SERVICE_BUS_CLUSTER_ID` | NATS cluster identifier | `simbuilder-local` | ✅ |
| **LLM Integration** | | | |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | `https://your-endpoint.openai.azure.com/` | ✅ |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | `your-openai-api-key` | ✅ |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-15-preview` | ✅ |
| `AZURE_OPENAI_MODEL_CHAT` | Chat completion model | `gpt-4o` | ✅ |
| `AZURE_OPENAI_MODEL_REASONING` | Text completion model | `gpt-4o` | ✅ |
| **Core API Service** | | | |
| `CORE_API_URL` | Core API base URL | `http://localhost:7000` | ✅ |
| `CORE_API_PORT` | Core API listening port | `7000` | ✅ |
| **Application Configuration** | | | |
| `LOG_LEVEL` | Application log level | `INFO` | ✅ |
| `ENVIRONMENT` | Runtime environment | `development` | ✅ |
| `DEBUG_MODE` | Enable debug features | `true` | ⚠️ |

### Docker Compose Infrastructure

The MVP requires the following containerized services for local development:

```yaml
# docker-compose.yml (key services)
services:
  neo4j:
    image: neo4j:5.11
    ports:
      - "7474:7474"  # HTTP Browser
      - "7687:7687"  # Bolt Protocol
    environment:
      - NEO4J_AUTH=neo4j/your-secure-password
      - NEO4J_apoc_export_file_enabled=true
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
    volumes:
      - neo4j_data:/data
      - ./plugins:/plugins

  nats:
    image: nats:2.10-alpine
    ports:
      - "4222:4222"  # Client connections
      - "8222:8222"  # Management UI
    command: ["--jetstream", "--store_dir=/data"]
    volumes:
      - nats_data:/data

  # Optional: Service Bus emulator for Azure Service Bus compatibility testing
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite
    ports:
      - "10000:10000"  # Blob service
    volumes:
      - azurite_data:/data

volumes:
  neo4j_data:
  nats_data:
  azurite_data:
```

### Shared Virtual Environment

All MVP components utilize a **shared virtual environment** located at the repository root under `.venv`. This approach:

- **Simplifies Dependency Management**: Single `requirements.txt` for all components
- **Reduces Disk Usage**: No duplicate package installations across components
- **Ensures Consistency**: All components use identical package versions
- **Streamlines Development**: Single environment activation for all development work

#### Virtual Environment Structure
```
simbuilder/
├── .venv/                     # Shared virtual environment
│   ├── bin/activate          # Environment activation script
│   ├── lib/python3.12/       # Installed packages
│   └── pyvenv.cfg            # Environment configuration
├── requirements.txt          # All dependencies for MVP
├── pyproject.toml           # Project metadata and build config
├── simbuilder/              # Source code packages
│   ├── config/              # Configuration Service
│   ├── graphdb/             # Graph Database Service
│   ├── servicebus/          # Service Bus
│   ├── spec_library/        # Spec Library
│   ├── core_api/            # Core API Service
│   ├── llm_foundry/         # LLM Foundry Integration
│   └── tenant_discovery/    # Tenant Discovery Agent
└── tests/                   # Test suites
```

### Running the MVP

#### Start Infrastructure Services
```bash
# Start all infrastructure containers
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
docker-compose logs -f neo4j  # Wait for "Started" message
```

#### Initialize and Start Application Services
```bash
# Activate shared environment
source .venv/bin/activate

# Initialize database schema
uv run python -m simbuilder.graphdb.schema --initialize

# Start Core API Service
uv run python -m simbuilder.core_api --port 7000 &

# Start Tenant Discovery Agent (when code is generated)
uv run python -m simbuilder.tenant_discovery --mode daemon &

# Verify all services are healthy
curl http://localhost:7000/health
curl http://localhost:7000/agents/status
```

#### Execute Tenant Discovery (Placeholder)
```bash
# Once implementation is complete, discovery will be initiated via:
uv run inv start-discovery --tenant-id $AZURE_TENANT_ID

# Or via API:
curl -X POST http://localhost:7000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "'$AZURE_TENANT_ID'", "type": "tenant_discovery"}'
```

### Integration Testing Setup

#### Verification Commands
```bash
# Test Azure CLI authentication
az account show --query "{subscriptionId: id, tenantId: tenantId}"

# Test Neo4j connectivity
echo "MATCH (n) RETURN count(n)" | uv run python -m simbuilder.graphdb.cli

# Test Service Bus connectivity
uv run python -c "
from simbuilder.servicebus import ServiceBusClient
client = ServiceBusClient()
print('Service Bus connectivity:', client.health_check())
"

# Test LLM integration
uv run python -c "
from simbuilder.llm_foundry import LLMClient
client = LLMClient.get_instance()
print('LLM connectivity:', client.health_check())
"
```

#### Integration Test Execution
```bash
# Run integration tests (once implemented)
uv run pytest tests/integration/ -v --tb=short

# Run end-to-end discovery test
uv run pytest tests/e2e/test_tenant_discovery.py -v --live-azure
```

### Troubleshooting

#### Common Setup Issues

**Azure Authentication Failures**
```bash
# Clear Azure CLI cache and re-authenticate
az logout
az cache purge
az login --tenant $AZURE_TENANT_ID
```

**Neo4j Connection Issues**
```bash
# Check Docker container status
docker-compose logs neo4j

# Verify port accessibility
telnet localhost 7687
```

**Service Bus Connection Issues**
```bash
# Check NATS container
docker-compose logs nats

# Verify NATS management UI
curl http://localhost:8222/varz
```

**Python Environment Issues**
```bash
# Recreate virtual environment
rm -rf .venv
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

**Success Criteria**: MVP success is defined as end-to-end tenant discovery completing without errors.