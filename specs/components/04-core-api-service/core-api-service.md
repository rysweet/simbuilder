# Core API Service Specification

## Purpose / Overview

The Core API Service serves as the central orchestration and coordination layer for SimBuilder, providing a unified REST API that coordinates all agent interactions, manages simulation lifecycle, and provides authentication/authorization. Built with FastAPI, it acts as the primary interface between user-facing applications (CLI, GUI, MCP) and the distributed agent architecture, ensuring consistent state management and workflow coordination.

## Functional Requirements / User Stories

- As a **CLI Interface**, I need a REST API to submit attack scenarios and monitor simulation progress
- As a **GUI Interface**, I need API endpoints to display simulation status, graphs, and management dashboards
- As an **MCP Service**, I need programmatic access to simulation creation, querying, and management
- As a **System Administrator**, I need API endpoints for user management, monitoring, and system configuration
- As **AI Agents**, I need authenticated API access to update simulation state and retrieve configuration
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
```
# Simulation Management
POST /api/v1/simulations - Create new simulation from attack scenario
GET /api/v1/simulations - List all simulations with filtering and pagination
GET /api/v1/simulations/{id} - Get detailed simulation information
PUT /api/v1/simulations/{id} - Update simulation configuration
DELETE /api/v1/simulations/{id} - Delete and cleanup simulation resources

# Workflow Management
POST /api/v1/simulations/{id}/start - Start simulation deployment
POST /api/v1/simulations/{id}/stop - Stop and cleanup simulation
GET /api/v1/simulations/{id}/status - Get current simulation status and progress
GET /api/v1/simulations/{id}/logs - Stream simulation logs and events

# Graph and Visualization
GET /api/v1/simulations/{id}/graph - Get graph visualization data
GET /api/v1/simulations/{id}/resources - List all deployed resources
GET /api/v1/simulations/{id}/costs - Get cost breakdown and projections

# Template and Library Management
GET /api/v1/templates/attacks - List attack pattern templates
GET /api/v1/templates/infrastructure - List infrastructure templates
POST /api/v1/templates - Upload new template to library

# System Management
GET /api/v1/health - System health check and service status
GET /api/v1/metrics - System metrics and performance data
POST /api/v1/agents/register - Register new agent with capabilities
GET /api/v1/agents - List registered agents and status
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
- **External Prompt Templates**: All AI agent prompts are externalized to Liquid template files under `prompts/` directory

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