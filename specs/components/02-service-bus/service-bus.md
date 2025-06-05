# Service Bus Specification

## Purpose / Overview

The Service Bus provides asynchronous message-based communication between SimBuilder agents and services using **CloudEvents-over-Protobuf** standard for message serialization. Built on Azure Service Bus for production and **NATS JetStream for local development**, it enables loosely coupled, scalable inter-agent communication with guaranteed message delivery, dead letter handling, and workflow orchestration. The service bus serves as the backbone for the agent workflow pipeline, ensuring reliable state transitions and coordination across the distributed simulation lifecycle.

## Functional Requirements / User Stories

- As an **Orchestrator Agent**, I need to publish workflow state changes to coordinate other agents
- As **AI Agents** (Clarifier, Planner, InfraSynthesis, DataSeeder, Validator), I need to receive workflow messages and publish completion notifications
- As a **Core API Service**, I need to monitor agent health and workflow progress through message tracking
- As a **System Administrator**, I need dead letter queue management for failed message processing
- As a **Developer**, I need message replay capabilities for debugging workflow issues
- As a **Monitoring System**, I need metrics and alerts for message throughput and agent responsiveness

## Interfaces / APIs

### Message Envelope Structure
All messages follow CloudEvents v1.0 standard with Protobuf serialization:
```yaml
CloudEvent Envelope:
  specversion: "1.0"
  type: "sim.workflow.v1" | "sim.health.v1" | "sim.error.v1"
  source: "agent://clarifier" | "agent://planner" | "service://core-api"
  id: "uuid-v4"
  time: "2023-12-01T10:00:00Z"
  datacontenttype: "application/protobuf"
  subject: "sim.workflow.clarifier.completed" # Hierarchical subject naming
  data: <protobuf-serialized-payload>
```

### Subject Naming Convention
- **Pattern**: `sim.<domain>.<component>.<action>`
- **Examples**:
  - `sim.workflow.v1.clarifier.started`
  - `sim.workflow.v1.planner.completed`
  - `sim.health.v1.agent.heartbeat`
  - `sim.error.v1.deployment.failed`

### Versioning Rules
- **Backward compatibility**: v1 messages must remain parseable by all agents
- **Version in subject**: Include version in message type (e.g., `sim.workflow.v1`)
- **Schema evolution**: Additive changes only; deprecated fields marked with `@deprecated`
- **Migration path**: 6-month overlap period for version transitions

### Inputs
- **Workflow Messages**: Agent state transitions, task assignments, and completion notifications
- **Health Check Messages**: Agent heartbeat and status updates
- **Error Messages**: Failed operations and retry requests
- **Configuration Messages**: Dynamic agent configuration updates
- **Cleanup Messages**: Simulation teardown and resource cleanup coordination

### Outputs
- **Message Delivery**: Guaranteed delivery to subscribed agents
- **Dead Letter Events**: Failed message notifications for manual intervention
- **Metrics**: Message throughput, queue depth, and processing latency
- **Audit Trail**: Message provenance and delivery confirmation

### Public REST / gRPC / CLI commands
```
POST /servicebus/topics/{topic}/messages - Send message to topic
GET /servicebus/topics/{topic}/subscriptions/{subscription}/messages - Receive messages
POST /servicebus/subscriptions/{subscription}/deadletter - Move message to dead letter queue
GET /servicebus/health - Service health and connection status
GET /servicebus/metrics - Queue depths, throughput, and latency metrics
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **Azure Service Bus**: Primary messaging infrastructure (production)
- **NATS JetStream**: Local development messaging broker
- **Core API Service**: Authentication and service registration
- **Graph Database Service**: Message state persistence and audit logging
- **Azure Key Vault**: Connection string and secret management
- **Azure Monitor**: Metrics collection and alerting
- **Proto Schema Directory**: `/proto/*.proto` - Protobuf message definitions for all service bus messages
- **Helper Library**: `sim_bus.py` - Unified message serialization/deserialization and broker abstraction

## Data Contracts / Schemas

### Message Types
```yaml
WorkflowMessage:
  headers: [message_id, correlation_id, timestamp, sender_id]
  body:
    workflow_id: string
    step: enum [clarification, planning, synthesis, deployment, seeding, validation]
    status: enum [started, completed, failed, retry]
    payload: object # step-specific data

AgentHealthMessage:
  headers: [agent_id, timestamp]
  body:
    status: enum [healthy, degraded, failed]
    metrics: object # performance and resource usage
    capabilities: array[string] # available agent functions

ErrorMessage:
  headers: [original_message_id, error_timestamp, retry_count]
  body:
    error_type: string
    error_message: string
    stack_trace: string
    recovery_action: enum [retry, manual_intervention, skip]
```

### Topic Structure
```yaml
Topics:
  - simulation-workflow # Main agent coordination
  - agent-health # Health monitoring and status
  - error-handling # Error notifications and recovery
  - cleanup-coordination # Resource cleanup orchestration

Subscriptions:
  simulation-workflow:
    - clarifier-agent
    - planner-agent
    - infrasynthesis-agent
    - orchestrator-agent
    - dataseeder-agent
    - validator-agent
  agent-health:
    - core-api-monitoring
    - operations-dashboard
```

## Documentation to Produce

- **Message Schema Reference**: Detailed schemas for all message types and topics
- **Agent Integration Guide**: How to connect agents to service bus topics
- **Dead Letter Queue Management**: Procedures for handling failed messages
- **Performance Tuning Guide**: Throughput optimization and scaling strategies
- **Monitoring and Alerting Setup**: Metrics collection and alert configuration
- **Disaster Recovery Procedures**: Service bus failover and message persistence

## Testing Strategy

### Unit Tests
- Message serialization and deserialization via `sim_bus.py` helper
- CloudEvents envelope validation and Protobuf parsing
- Topic and subscription management
- Dead letter queue handling
- Connection resilience and retry logic
- Message filtering and routing
- Authentication and authorization

### Integration Tests
- **Docker-compose NATS startup for CI**: Automated NATS JetStream container orchestration
- **Live Azure Service Bus required for production tests** - no mocking of messaging infrastructure
- End-to-end workflow orchestration with real agents
- Multi-agent concurrent message processing
- Dead letter queue processing and message replay
- Failover scenarios with service bus disruption
- Message ordering and duplicate detection
- **Cross-broker compatibility**: Ensure identical behavior between NATS (dev) and Azure Service Bus (prod)

### Acceptance Tests
- Complete simulation workflow message flow
- Agent coordination under high load conditions
- Message delivery guarantees during agent failures
- Dead letter queue management and recovery procedures
- Performance benchmarks with 10+ concurrent simulations

## Acceptance Criteria

- **Reliability**: 99.9% message delivery with duplicate detection and dead letter handling
- **Performance**: Process 1000+ messages/minute with sub-100ms latency
- **Scalability**: Support 20+ concurrent agents across multiple simulation workflows
- **Security**: Encrypted message transport with SAS token authentication
- **Monitoring**: Real-time metrics for queue depth, throughput, and error rates
- **Recovery**: Automatic retry with exponential backoff and manual dead letter intervention
- **Audit**: Complete message trail for compliance and debugging
- **Message Serialization**: All messages serialize/deserialize correctly via `sim_bus.py` helper library
- **Broker Parity**: Identical behavior and message delivery guarantees between NATS JetStream (local dev) and Azure Service Bus (production)
- **CloudEvents Compliance**: All messages conform to CloudEvents v1.0 specification with Protobuf payload encoding

## Open Questions

- Should we implement message partitioning for agent-specific processing optimization?
- What is the optimal message retention period for audit and replay capabilities?
- How should we handle message ordering requirements across different workflow steps?
- Should we implement priority queues for urgent operations like cost limit violations?
- What disaster recovery strategy should we use for cross-region service bus failover?
- How do we handle schema evolution for messages without breaking existing agents?
- Should we implement request-response patterns or stick to fire-and-forget messaging?