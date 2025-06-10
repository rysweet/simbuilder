# REST API Gateway Specification

## Session ID Handling and Dynamic Port Allocation

The REST API Gateway supports multi-instance deployment through session-aware configuration and
dynamic port allocation, enabling multiple SimBuilder instances to operate concurrently without
conflicts.

### Session-Aware Features

- **Dynamic Port Binding**: Uses `API_GATEWAY_PORT` environment variable for runtime port allocation
- **Session Context Headers**: Automatically includes session ID in all downstream service requests
- **Service Discovery**: Routes to session-specific backend services using allocated ports
- **Health Checks**: Session-aware health monitoring of connected services
- **Load Balancing**: Session-isolated request routing and load distribution

### Environment Configuration

```bash
# Session identification and networking
SIMBUILDER_SESSION_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
API_GATEWAY_PORT=18080
COMPOSE_PROJECT_NAME=simbuilder-a1b2c3d4

# Backend service connections with dynamic ports
CORE_API_URL=http://localhost:${CORE_API_PORT}
NEO4J_HTTP_URI=http://localhost:${GRAPH_DB_HTTP_PORT}
NATS_MANAGEMENT_URL=http://localhost:${NATS_HTTP_PORT}
```

### Container Configuration

```yaml
api-gateway:
  container_name: ${COMPOSE_PROJECT_NAME}-api-gateway
  ports:
    - "${API_GATEWAY_PORT}:8080"
  environment:
    - SIMBUILDER_SESSION_ID=${SIMBUILDER_SESSION_ID}
    - BACKEND_SERVICES_PREFIX=${COMPOSE_PROJECT_NAME}
  networks:
    - ${COMPOSE_PROJECT_NAME}-network
```

## Purpose / Overview

The REST API Gateway component provides a unified external API interface for third-party
integrations and external systems to interact with SimBuilder. It handles authentication,
authorization, rate limiting, API versioning, and request routing while maintaining security
isolation between external clients and internal SimBuilder components. This gateway enables
enterprise integration scenarios and supports automated CI/CD pipelines that need to interact with
simulation environments.

## Functional Requirements / User Stories

- As an **External Developer**, I need a stable REST API to integrate SimBuilder with third-party
  security tools and workflows
- As a **DevOps Engineer**, I need API endpoints to automate simulation creation and management in
  CI/CD pipelines
- As an **Enterprise Architect**, I need standardized API patterns for integrating SimBuilder with
  enterprise security orchestration platforms
- As a **Security Operations Center**, I need API access to trigger simulations based on threat
  intelligence feeds
- As a **Compliance Officer**, I need API audit trails and access controls for external system
  interactions
- As a **Partner Organization**, I need secure API access to leverage SimBuilder capabilities in my
  own security products
- As a **API Consumer**, I need comprehensive API documentation, examples, and SDKs for rapid
  integration
- As a **System Administrator**, I need rate limiting and access controls to prevent API abuse and
  ensure system stability

## Interfaces / APIs

### Inputs

- **External API Requests**: RESTful HTTP requests from third-party clients and integrations
- **Authentication Tokens**: OAuth 2.0, API keys, and JWT tokens for client authentication
- **Authorization Policies**: Role-based access control and permission configurations
- **Rate Limiting Rules**: API throttling and quota management configurations
- **Integration Specifications**: Third-party system integration requirements and mappings

### Outputs

- **Standardized API Responses**: JSON responses following OpenAPI 3.0 specifications
- **Authentication Results**: Token validation and user authorization status
- **API Metrics**: Usage analytics, performance metrics, and rate limiting statistics
- **AuditLogs**: Complete API access logs for security and compliance monitoring
- **Integration Status**: Health and connectivity status for external system integrations

### Public Endpoints / CLI Commands

```
# Simulation Management
POST /api/v1/simulations - Create new simulation environment
GET /api/v1/simulations - List all accessible simulations
GET /api/v1/simulations/{id} - Retrieve simulation details and status
PUT /api/v1/simulations/{id} - Update simulation configuration
DELETE /api/v1/simulations/{id} - Terminate and cleanup simulation

# Authentication and Authorization
POST /api/v1/auth/token - Obtain API access token
POST /api/v1/auth/refresh - Refresh expired access token
GET /api/v1/auth/permissions - Retrieve user permissions and scopes

# Integration and Webhooks
POST /api/v1/webhooks - Register webhook endpoints for event notifications
GET /api/v1/integrations - List available third-party integrations
POST /api/v1/integrations/{type} - Configure specific integration

# Monitoring and Analytics
GET /api/v1/metrics - Retrieve API usage metrics and analytics
GET /api/v1/health - Gateway health check and system status
GET /api/v1/audit - Retrieve API access audit logs
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: For proxying LLM requests from external clients
- **Core API Service**: Backend SimBuilder functionality and business logic
- **Azure API Management**: Enterprise API gateway features and security
- **Azure Active Directory**: Authentication provider and identity management
- **Graph Database Service**: For storing API access patterns and relationships
- **Service Bus**: For asynchronous processing of external requests
- **Azure Key Vault**: For secure storage of API keys and integration credentials
- **Azure Monitor**: For API performance monitoring and alerting
- **OpenAPI Generator**: For client SDK generation and documentation

## Data Contracts / Schemas

### API Request/Response Schema

```yaml
SimulationRequest:
  simulation_name: string
  attack_description: string
  environment_requirements:
    resource_types: array[string]
    scale_requirements: ScaleSpec
    compliance_requirements: array[string]
  notification_preferences:
    webhook_url: string
    email_notifications: boolean
    completion_callback: string
  metadata:
    external_system_id: string
    correlation_id: string
    tags: object

SimulationResponse:
  simulation_id: string
  status: enum [PENDING, PROVISIONING, READY, RUNNING, COMPLETED, FAILED]
  created_at: datetime
  estimated_completion: datetime
  resource_endpoints:
    management_url: string
    telemetry_dashboard: string
    api_endpoints: array[string]
  cost_information:
    estimated_cost: decimal
    current_spend: decimal
    budget_remaining: decimal
```

### Authentication Schema

```yaml
AuthenticationRequest:
  grant_type: enum [client_credentials, authorization_code, refresh_token]
  client_id: string
  client_secret: string
  scope: array[string]
  redirect_uri: string

AuthenticationResponse:
  access_token: string
  token_type: string
  expires_in: integer
  refresh_token: string
  scope: array[string]
  permissions: array[Permission]

Permission:
  resource: string
  actions: array[string]
  conditions: array[Condition]
```

### Rate Limiting Schema

```yaml
RateLimitPolicy:
  client_id: string
  tier: enum [FREE, BASIC, PREMIUM, ENTERPRISE]
  limits:
    requests_per_minute: integer
    requests_per_hour: integer
    requests_per_day: integer
    concurrent_simulations: integer
  quotas:
    monthly_api_calls: integer
    storage_quota_gb: integer
    compute_hours: integer
```

## Documentation to Produce

- **OpenAPI 3.0 Specification**: Complete API documentation with examples and schemas
- **Integration Guide**: Step-by-step integration instructions for common scenarios
- **Authentication Manual**: OAuth 2.0 flow implementation and token management
- **SDK Documentation**: Generated client libraries for popular programming languages
- **Rate Limiting Guide**: API throttling policies and quota management
- **Webhook Integration Manual**: Event-driven integration patterns and callback handling

## Testing Strategy

### Unit Tests

- API endpoint routing and request validation
- Authentication and authorization logic
- Rate limiting and throttling mechanisms
- Request/response transformation and formatting
- Error handling and status code generation
- API versioning and backward compatibility

### Integration Tests

- **Live external system integration** - no mocking of third-party services
- Complete API workflow testing with real authentication providers
- Rate limiting enforcement with actual traffic simulation
- Webhook delivery and callback processing
- API gateway performance under load
- Cross-component integration with Core API Service

### End-to-End Acceptance Tests

- Full external integration scenarios with realistic API consumers
- Complex simulation lifecycle management via API
- Authentication and authorization across multiple client types
- API documentation accuracy and SDK functionality validation
- Compliance audit trail generation and verification

## Acceptance Criteria

- **API Performance**: Sub-200ms response times for 95% of API requests
- **Availability**: 99.9% uptime with automatic failover and load balancing
- **Security**: Zero API security vulnerabilities with comprehensive authentication
- **Rate Limiting**: Accurate enforcement of API quotas and throttling policies
- **Documentation**: 100% API coverage with up-to-date OpenAPI documentation
- **Integration Support**: Working SDKs for 5+ major programming languages
- **Scalability**: Support 1000+ concurrent API clients with linear scaling
- **Compliance**: Complete audit trail for all API access and operations
- **Backward Compatibility**: API versioning with 12-month deprecation cycles

## Open Questions

- What API versioning strategy should we implement for long-term backward compatibility?
- Should we implement GraphQL endpoints alongside REST for complex query scenarios?
- How should we handle API schema evolution and client notification of changes?
- What caching strategies should we implement for frequently accessed API endpoints?
- Should we implement API marketplace capabilities for third-party developers?
- How do we handle bulk operations and batch API requests efficiently?
- What monitoring and analytics should we provide to API consumers for their usage patterns?
- Should we implement API sandboxing capabilities for testing and development scenarios?
