# Core API Service Specification

## Session ID Handling and Dynamic Port Allocation

The Core API Service supports multi-instance deployment through session-aware configuration and
dynamic port allocation, enabling multiple SimBuilder instances to run concurrently without
conflicts.

### Session-Aware Features

- **Dynamic Port Binding**: Uses `API_GATEWAY_PORT` environment variable for conflict-free port
  allocation
- **Session Context**: Maintains session ID in request context for downstream service communication
- **Database Connections**: Uses session-specific connection strings with allocated ports
- **Service Discovery**: Routes requests to session-specific backend services
- **Container Naming**: Follows `simbuilder-api-<session_id_short>` naming convention

### Environment Variables

```bash
# Session identification
SIMBUILDER_SESSION_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
API_GATEWAY_PORT=18080

# Session-specific service connections
NEO4J_URI=bolt://localhost:${GRAPH_DB_BOLT_PORT}
NATS_URL=nats://localhost:${NATS_CLIENT_PORT}
```

## Purpose / Overview

The Core API Service serves as the central orchestration and coordination layer for SimBuilder,
providing a unified REST API that coordinates all agent interactions, manages simulation lifecycle,
and provides authentication/authorization. Built with FastAPI, it acts as the primary interface
between user-facing applications (CLI, GUI, MCP) and the distributed agent architecture, ensuring
consistent state management and workflow coordination.

## Functional Requirements / User Stories

- As a **CLI Interface**, I need a REST API to submit attack scenarios and monitor simulation
  progress
- As a **GUI Interface**, I need API endpoints to display simulation status, graphs, and management
  dashboards
- As an **MCP Service**, I need programmatic access to simulation creation, querying, and management
- As a **System Administrator**, I need API endpoints for user management, monitoring, and system
  configuration
- As **AI Agents**, I need authenticated API access to update simulation state and retrieve
  configuration
- As a **Security Team**, I need audit logging and access control for all API operations
- As a **Developer**, I need comprehensive API documentation and testing capabilities

## Interfaces / APIs

### Inputs

- **Attack Scenarios**: Text descriptions or structured specifications for simulation creation
- **User Authentication**: OAuth2/JWT tokens for API access control
- **Agent Registration**: Agent service discovery and capability registration
- **Configuration Updates**: System settings, thresholds, and operational parameters
- **Query Requests**: Simulation status, graph data, and reporting requests

### Outputs

- **REST API Responses**: JSON responses with simulation data, status, and metadata
- **WebSocket Events**: Real-time updates for simulation progress and agent status
- **Authentication Tokens**: JWT tokens for service-to-service communication
- **API Documentation**: OpenAPI/Swagger specifications and interactive documentation
- **Audit Logs**: Structured logging for all API operations and access patterns

### Public REST / gRPC / CLI commands

```http
# Simulation Management
POST /api/v1/simulations
  - Create new simulation from attack scenario
  - Request: SimulationRequest
  - Response: SimulationResponse
  - Consumer: CLI Interface, GUI Interface, MCP Service

GET /api/v1/simulations
  - List all simulations with filtering and pagination
  - Query params: status, created_after, created_before, limit, offset
  - Response: {"simulations": [SimulationResponse], "total": 150, "offset": 0}
  - Consumer: GUI Interface, Operations Dashboard

GET /api/v1/simulations/{id}
  - Get detailed simulation information
  - Response: SimulationResponse with full details
  - Consumer: CLI Interface, GUI Interface, Agents

PUT /api/v1/simulations/{id}
  - Update simulation configuration
  - Request: Partial SimulationRequest
  - Response: SimulationResponse
  - Consumer: GUI Interface, Operations Dashboard

DELETE /api/v1/simulations/{id}
  - Delete and cleanup simulation resources
  - Response: {"status": "deleted", "cleanup_jobs": ["job1", "job2"]}
  - Consumer: CLI Interface, GUI Interface, Auto-cleanup

# Workflow Management
POST /api/v1/simulations/{id}/start
  - Start simulation deployment
  - Request: {"force_restart": false}
  - Response: {"status": "started", "workflow_id": "uuid"}
  - Consumer: CLI Interface, GUI Interface, Orchestrator Agent

POST /api/v1/simulations/{id}/stop
  - Stop and cleanup simulation
  - Request: {"immediate": false, "preserve_data": true}
  - Response: {"status": "stopping", "estimated_completion": "2023-12-01T15:30:00Z"}
  - Consumer: CLI Interface, GUI Interface, Emergency Controls

GET /api/v1/simulations/{id}/status
  - Get current simulation status and progress
  - Response: {"status": "deploying", "progress": 65, "current_step": "infrasynthesis", "eta": "2023-12-01T14:00:00Z"}
  - Consumer: CLI Interface, GUI Interface, Monitoring

GET /api/v1/simulations/{id}/logs
  - Stream simulation logs and events via WebSocket
  - Response: Stream of {"timestamp": "...", "level": "info", "message": "...", "component": "clarifier"}
  - Consumer: CLI Interface, GUI Interface, Operations Dashboard

# Graph and Visualization
GET /api/v1/simulations/{id}/graph
  - Get graph visualization data for force-directed layouts
  - Response: {"nodes": [...], "edges": [...], "layout": "force-directed"}
  - Consumer: GUI Interface

GET /api/v1/simulations/{id}/resources
  - List all deployed resources with current status
  - Response: {"resources": [ResourceSummary], "cost_estimate": "$45.20/hour"}
  - Consumer: GUI Interface, Operations Dashboard, Cost Management

GET /api/v1/simulations/{id}/costs
  - Get detailed cost breakdown and projections
  - Response: CostBreakdown with hourly/daily/monthly projections
  - Consumer: GUI Interface, Operations Dashboard, FinOps

# Template and Library Management
GET /api/v1/templates/attacks
  - List available attack pattern templates
  - Query params: category, severity, mitre_technique
  - Response: {"templates": [AttackTemplate], "categories": ["lateral-movement"]}
  - Consumer: CLI Interface, GUI Interface, Clarifier Agent

GET /api/v1/templates/infrastructure
  - List IaC templates in spec library
  - Query params: provider, category, complexity
  - Response: {"templates": [InfraTemplate], "providers": ["terraform", "bicep"]}
  - Consumer: Planner Agent, InfraSynthesis Agent

POST /api/v1/templates
  - Upload new template to library
  - Request: {"type": "attack|infrastructure", "template": TemplateSpec}
  - Response: {"template_id": "uuid", "status": "validated"}
  - Consumer: Template Authors, GUI Interface

# System Management
GET /api/v1/health
  - System health check and service status
  - Response: {"status": "healthy", "services": {"graph_db": "healthy", "service_bus": "healthy"}}
  - Consumer: Load Balancers, Monitoring Systems

GET /api/v1/metrics
  - System metrics and performance data
  - Response: {"active_simulations": 12, "avg_response_time_ms": 145, "error_rate": 0.01}
  - Consumer: Operations Dashboard, Monitoring Systems

POST /api/v1/agents/register
  - Register new agent with capabilities
  - Request: AgentRegistration
  - Response: {"agent_id": "uuid", "status": "registered", "assigned_capabilities": [...]}
  - Consumer: Agent Services, Orchestrator

GET /api/v1/agents
  - List registered agents and their current status
  - Response: {"agents": [AgentStatus], "total_healthy": 6, "total_registered": 7}
  - Consumer: Operations Dashboard, Health Monitoring
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **FastAPI**: Primary web framework for REST API implementation
- **Graph Database Service**: Simulation metadata and state storage
- **Service Bus**: Agent communication and workflow coordination
- **Spec Library**: Template and specification management
- **Azure Active Directory**: User authentication and authorization
- **Azure Key Vault**: API keys and service credential management
- **Redis**: Session management and caching layer
- **External Prompt Templates**: All AI agent prompts are externalized to Liquid template files
  under `prompts/` directory

## Data Contracts / Schemas

### API Request/Response Models

```python
class SimulationRequest(BaseModel):
    name: str
    description: str
    attack_scenario: str
    budget_limit: Optional[float] = None
    ttl_hours: Optional[int] = 24
    tags: List[str] = []


class SimulationResponse(BaseModel):
    id: str
    name: str
    status: SimulationStatus
    created_at: datetime
    updated_at: datetime
    progress: float
    estimated_completion: Optional[datetime]
    costs: CostBreakdown
    resources: List[ResourceSummary]


class SimulationStatus(str, Enum):
    CREATED = "created"
    CLARIFYING = "clarifying"
    PLANNING = "planning"
    SYNTHESIZING = "synthesizing"
    DEPLOYING = "deploying"
    SEEDING = "seeding"
    VALIDATING = "validating"
    READY = "ready"
    FAILED = "failed"
    CLEANUP = "cleanup"


class AgentRegistration(BaseModel):
    agent_id: str
    agent_type: str
    capabilities: List[str]
    endpoint: str
    health_check_url: str
```

### Authentication and Authorization

```python
class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]


class APIKey(BaseModel):
    key_id: str
    name: str
    permissions: List[str]
    expires_at: Optional[datetime]
```

## Documentation to Produce

- **OpenAPI Specification**: Complete API documentation with examples and schemas
- **Authentication Guide**: OAuth2 flow, JWT token management, and API key usage
- **Agent Integration Guide**: How agents register and interact with the Core API
- **Rate Limiting and Throttling**: API usage limits and best practices
- **Error Handling Reference**: Error codes, retry strategies, and troubleshooting
- **Deployment Guide**: Configuration, scaling, and operational procedures

## Testing Strategy

### Unit Tests

- API endpoint functionality and parameter validation
- Authentication and authorization logic
- Request/response serialization and deserialization
- Error handling and edge cases
- Rate limiting and throttling mechanisms
- WebSocket connection management

### Integration Tests

- **Live dependency services required** - no mocking of Graph DB, Service Bus, or Spec Library
- End-to-end simulation creation and management workflows
- Agent registration and communication patterns
- Authentication integration with Azure AD
- Concurrent API access and thread safety
- Performance testing under high load conditions

### Acceptance Tests

- Complete simulation lifecycle through API calls
- Multi-user concurrent access and data isolation
- Real-time updates via WebSocket connections
- API rate limiting and security controls
- System monitoring and health check reliability

## Acceptance Criteria

- **Performance**: Handle 100+ concurrent API requests with sub-200ms response times
- **Reliability**: 99.9% uptime with graceful degradation during dependency failures
- **Security**: OWASP compliance with authentication, authorization, and audit logging
- **Scalability**: Horizontal scaling support with stateless design and load balancing
- **Documentation**: Comprehensive OpenAPI spec with interactive testing capabilities
- **Monitoring**: Health checks, metrics collection, and distributed tracing
- **Compliance**: Audit logging meets enterprise security and compliance requirements

## Open Questions

- Should we implement GraphQL endpoints alongside REST for complex query requirements?
- What rate limiting strategy balances usability with system protection?
- How should we handle long-running operations with polling vs. WebSocket updates?
- Should we implement API versioning strategy for backward compatibility?
- What caching strategy optimizes performance while maintaining data consistency?
- How do we handle service mesh integration for inter-service communication?
- Should we implement request queuing for handling traffic spikes?
- What authentication method should we use for agent-to-API communication?
