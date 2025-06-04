# Graph Database Service Specification

## Purpose / Overview

The Graph Database Service provides the central data store for SimBuilder's metadata, relationships, and simulation state management. Built on Neo4j, it maintains the complete graph representation of simulation environments, including resources, dependencies, configurations, and deployment states. This service serves as the single source of truth for all simulation metadata and enables complex relationship queries across tenants, identities, workloads, and attack patterns.

## Functional Requirements / User Stories

- As a **Core API Service**, I need to persist and query simulation metadata in a graph structure to track complex relationships between resources
- As a **Clarifier Agent**, I need to store partial attack specifications and incrementally build complete models through clarification sessions
- As a **Planner Agent**, I need to query existing patterns and store resource plans with dependency relationships
- As a **InfraSynthesis Agent**, I need to validate resource dependencies and store deployment manifests with their relationships
- As a **DataSeeder Agent**, I need to record seeded data relationships across tenants and workloads
- As a **Validator Agent**, I need to query environment state and validate against expected telemetry configurations
- As a **GUI Interface**, I need to retrieve graph data for visualization using force-directed graph layouts
- As an **Operations team**, I need to query simulation costs, usage patterns, and cleanup schedules

## Interfaces / APIs

### Inputs
- **AttackSpec objects**: Structured attack scenario data with entities and relationships
- **ResourcePlan objects**: Infrastructure plans with dependency graphs
- **DeploymentManifest objects**: Deployed infrastructure state and configuration
- **TelemetrySchema objects**: Expected telemetry collection points and relationships
- **User queries**: Cypher queries for complex relationship traversal
- **Cleanup requests**: Deletion of simulation nodes and relationships

### Outputs
- **Graph query results**: JSON responses with nodes, relationships, and properties
- **Visualization data**: Graph structure optimized for force-directed rendering
- **Relationship traversals**: Dependency chains, impact analysis, and path queries
- **Aggregation reports**: Cost summaries, resource utilization, and pattern analysis

### Public REST / gRPC / CLI commands
```
POST /graph/nodes - Create nodes with properties and labels
POST /graph/relationships - Create relationships between nodes
GET /graph/query - Execute Cypher queries
GET /graph/visualize/{simulation_id} - Get visualization-ready graph data
DELETE /graph/simulation/{id} - Remove all nodes/relationships for a simulation
GET /graph/health - Health check and connection status
```

## Dependencies

- **Neo4j Database**: Core graph database engine (v5.x)
- **Azure Service Bus**: For receiving state update messages from agents
- **Core API Service**: Authentication and authorization validation
- **Docker/Podman**: For containerized deployment
- **Azure Storage**: For backup and disaster recovery

## Data Contracts / Schemas

### Node Types
```yaml
Simulation:
  properties: [id, name, status, created_at, budget_limit, ttl]
  labels: [Simulation]

AttackPattern:
  properties: [id, name, type, severity, mitre_tactics]
  labels: [AttackPattern]

AzureResource:
  properties: [id, type, region, status, cost, tags]
  labels: [AzureResource, Tenant, VM, Network, etc.]

Identity:
  properties: [id, type, tenant_id, privileges, synthetic]
  labels: [Identity, User, ServicePrincipal]

TelemetryPoint:
  properties: [id, type, schema, collection_endpoint]
  labels: [TelemetryPoint, LogAnalytics, Sentinel]
```

### Relationship Types
```yaml
DEPENDS_ON: Resource dependencies and deployment order
CONTAINS: Hierarchical containment (tenant contains resources)
MONITORS: Telemetry collection relationships
TARGETS: Attack pattern to target resource mapping
SEEDS: Data seeding relationships between identities and resources
VALIDATES: Validation requirements between components
```

## Documentation to Produce

- **Neo4j Schema Documentation**: Node types, relationship types, and properties
- **API Reference**: REST endpoint documentation with examples
- **Query Cookbook**: Common Cypher patterns for simulation management
- **Backup/Recovery Procedures**: Data protection and disaster recovery
- **Performance Tuning Guide**: Indexing strategies and query optimization
- **Graph Visualization Guide**: Integration patterns for GUI components

## Testing Strategy

### Unit Tests
- Neo4j connection management and failover
- CRUD operations for all node and relationship types
- Cypher query builder and parameter binding
- Data validation and constraint enforcement
- Backup and restore functionality
- Performance benchmarks for common query patterns

### Integration Tests
- **Live Neo4j instance required** - no mocking of database layer
- End-to-end simulation lifecycle with real graph operations
- Service Bus integration for state updates from agents
- Concurrent access patterns with multiple agent connections
- Large graph performance with 1000+ node simulations
- Disaster recovery with actual backup/restore cycles

### Acceptance Tests
- Complete simulation graph creation and traversal
- Graph visualization data export for GUI rendering
- Complex dependency resolution for multi-tenant scenarios
- Cost aggregation and reporting accuracy
- Cleanup operations maintain referential integrity

## Acceptance Criteria

- **Performance**: Support 10+ concurrent simulations with sub-second query response
- **Scalability**: Handle graphs with 10,000+ nodes and 50,000+ relationships per simulation
- **Reliability**: 99.9% uptime with automatic failover and data replication
- **Data Integrity**: ACID transactions with referential integrity constraints
- **Security**: Encrypted connections, role-based access control, audit logging
- **Backup**: Automated daily backups with point-in-time recovery capabilities
- **Monitoring**: Health checks, performance metrics, and alerting integration

## Open Questions

- Should we implement graph partitioning strategies for multi-tenant isolation?
- What is the optimal indexing strategy for frequent relationship traversals?
- How should we handle schema evolution and migration for existing simulations?
- Should we implement read replicas for visualization queries vs. transactional operations?
- What backup retention policy aligns with simulation lifecycle requirements?
- How do we handle concurrent modifications to the same simulation graph?