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

---

**Success Criteria**: MVP success is defined as end-to-end tenant discovery completing without errors.