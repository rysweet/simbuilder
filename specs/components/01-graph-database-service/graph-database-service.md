# Graph Database Service Specification

## Purpose / Overview

The Graph Database Service serves as the foundational data layer for SimBuilder, providing sophisticated graph-based storage and querying capabilities specifically designed for simulation data management. This service leverages the natural graph structure of cloud infrastructure relationships to enable efficient storage, retrieval, and analysis of complex simulation scenarios.

As the central repository for all simulation-related data, the service manages intricate relationships between infrastructure components, deployment dependencies, user interactions, and temporal simulation states. The graph-based approach allows for intuitive representation of multi-tenant cloud environments, resource hierarchies, and cross-service dependencies that are fundamental to accurate infrastructure simulations.

**Core Value Propositions:**
- **Natural Relationship Modeling**: Graph structure inherently represents infrastructure dependencies and relationships
- **Performance at Scale**: Optimized for complex queries across large simulation datasets
- **Real-time Operations**: Supports live simulation state management and updates
- **Historical Intelligence**: Maintains comprehensive audit trails and enables trend analysis
- **Ecosystem Integration**: Seamlessly integrates with all SimBuilder components through standardized interfaces

The service is designed to run in a container locally or in Azure Container Apps, with mounted `plugins/` directory for APOC and vector search extensions, and persistent data storage in a named volume `neo4j_data`.

**Key Capabilities:**
- Ingest and store Azure tenant resource graphs produced by the Tenant Discovery Agent
- Support complex relationship queries across multi-tenant environments with sub-second response times
- Maintain simulation state and metadata integrity with ACID compliance
- Provide semantic search through vector indexes and embeddings using GDS similarity functions
- Enable efficient storage and retrieval of various node types (AST, filesystem, documentation, summaries)
- Support both synchronous and asynchronous query execution patterns
- Manage connection lifecycle with retry mechanisms for transient failures
- Advanced analytics support for simulation pattern recognition
- Multi-tenant data isolation and security
- Real-time state management during active simulation execution

## Functional Requirements / User Stories

### Core Data Management
- **FR-1**: Store and manage comprehensive simulation metadata including configurations, parameters, execution context, and environmental variables
- **FR-2**: Maintain complex multi-dimensional relationships between infrastructure components including dependencies, hierarchies, associations, and temporal relationships
- **FR-3**: Support real-time data updates during simulation execution with zero-downtime operations and consistent performance
- **FR-4**: Provide sophisticated querying capabilities including graph traversal, pattern matching, and analytical queries with sub-second response times
- **FR-5**: Implement comprehensive data versioning, historical tracking, point-in-time recovery, and audit capabilities for compliance and debugging

### Advanced Graph Operations
- **FR-6**: Execute complex graph algorithms for dependency analysis, impact assessment, and optimization recommendations
- **FR-7**: Support graph pattern recognition for identifying common infrastructure configurations and anti-patterns
- **FR-8**: Provide path analysis capabilities for understanding deployment workflows and dependency chains
- **FR-9**: Enable graph-based analytics for simulation performance optimization and resource utilization analysis

### Integration and Ecosystem Support
- **FR-10**: Integrate seamlessly with Service Bus for event-driven data updates and real-time synchronization
- **FR-11**: Support Core API Service queries and complex data operations with standardized interfaces
- **FR-12**: Enable secure data access for various SimBuilder agents with role-based permissions
- **FR-13**: Provide standardized GraphQL and REST interfaces for ecosystem components
- **FR-14**: Support real-time data streaming for live simulation monitoring and dashboards

### Performance, Scalability, and Reliability
- **FR-15**: Handle concurrent read/write operations from multiple simulation instances with linear scalability
- **FR-16**: Scale horizontally to accommodate enterprise-level simulation complexity and volume
- **FR-17**: Maintain query response times under 50ms for standard operations and under 200ms for complex analytical queries
- **FR-18**: Support large-scale simulations with tens of thousands of infrastructure components and millions of relationships
- **FR-19**: Provide 99.9% uptime with automated failover and disaster recovery capabilities
- **FR-20**: Implement intelligent caching and query optimization for enhanced performance

### SimBuilder-Specific Use Cases
- As a **Core API Service**, I need to persist and query simulation metadata in a graph structure to track complex relationships between resources
- As a **Clarifier Agent**, I need to store partial attack specifications and incrementally build complete models through clarification sessions
- As a **Planner Agent**, I need to query existing patterns and store resource plans with dependency relationships
- As a **InfraSynthesis Agent**, I need to validate resource dependencies and store deployment manifests with their relationships
- As a **DataSeeder Agent**, I need to record seeded data relationships across tenants and workloads
- As a **Validator Agent**, I need to query environment state and validate against expected telemetry configurations
- As a **GUI Interface**, I need to retrieve graph data for visualization using force-directed graph layouts
- As an **Operations team**, I need to query simulation costs, usage patterns, and cleanup schedules
- As a **developer**, I want to easily execute Cypher queries against the graph service so that I can retrieve and manipulate graph data
- As a **developer**, I want reliable connection handling so that transient database issues don't crash my application
- As a **developer**, I want to use vector search for semantic similarity so that I can find related code elements by meaning
- As a **developer**, I want async-compatible database access so I can use it with FastAPI endpoints

## Technical Stack

### Database Technology
- **Primary Database**: Neo4j Enterprise Edition 5.x
  - Native graph database with APOC (Awesome Procedures on Cypher) for advanced algorithms
  - Full ACID compliance with distributed transaction support
  - Causal clustering with read replicas for high availability and read scaling
  - Advanced security features including fine-grained access control for multi-tenant environments
  - Graph Data Science Library for advanced analytics and machine learning capabilities

### Runtime and Infrastructure
- **Container Platform**: Kubernetes with Helm charts for deployment management
- **Language**: Java 21 LTS with virtual threads for enhanced performance
- **API Framework**: Spring Boot 3.2+ with Spring Data Neo4j 7.x
- **Message Queue Integration**: Apache Kafka client libraries with schema registry support
- **Service Mesh**: Istio for secure service-to-service communication and observability

### Performance and Optimization
- **Caching Layer**: Redis Enterprise for query result caching and session management
- **Connection Pooling**: HikariCP with optimized connection management
- **Query Optimization**: Cypher query profiling and automatic index recommendations
- **Load Balancing**: NGINX with intelligent routing for read/write split operations

### Supporting Technologies
- **Monitoring and Observability**:
  - Prometheus metrics with custom business metrics
  - Grafana dashboards with alerting
  - OpenTelemetry for distributed tracing
  - Neo4j Browser and Bloom for graph visualization
- **Logging**: Structured logging with ELK stack integration and correlation IDs
- **Security**:
  - JWT token validation with refresh token support
  - RBAC implementation with fine-grained permissions
  - TLS 1.3 encryption for all communications
  - Secrets management via Azure Key Vault integration
- **Backup and Recovery**:
  - Automated incremental backups with configurable retention policies
  - Point-in-time recovery capabilities
  - Cross-region backup replication for disaster recovery
  - Backup verification and integrity testing

## Technical Architecture

### Neo4jConnector Interface

The [`Neo4jConnector`](neo4j_connector.py:1) class provides a unified interface for interacting with Neo4j, supporting both synchronous and asynchronous operations:

```python
class Neo4jConnector:
    def __init__(self, uri=None, username=None, password=None, **config_options):
        """Initialize connector with connection parameters from env vars or args."""
        
    # Synchronous methods
    def execute_query(self, query, params=None, write=False, retry_count=3):
        """Execute a Cypher query with automatic connection management."""
        
    def execute_many(self, queries, params_list=None, write=False):
        """Execute multiple queries in a single transaction."""
    
    # Asynchronous methods
    async def execute_query_async(self, query, params=None, write=False):
        """Execute a Cypher query asynchronously."""
        
    async def check_connection_async(self):
        """Check database connectivity asynchronously."""
        
    async def close_async(self):
        """Close connections asynchronously."""
    
    # Schema management
    def initialize_schema(self):
        """Create constraints, indexes, and schema elements."""
        
    def create_vector_index(self, label, property_name, dimensions, similarity="cosine"):
        """Create a vector index for semantic search."""
    
    # Vector search
    def semantic_search(self, query_embedding, node_label, limit=10):
        """Perform vector similarity search using the provided embedding."""
    
    # Connection management
    def check_connection(self):
        """Check if database is accessible and return basic info."""
        
    def close(self):
        """Close all connections in the pool."""
        
    # Context manager support
    def __enter__(self):
        """Support for context manager protocol."""
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
```

### Connection Management

The [`Neo4jConnector`](neo4j_connector.py:1) implements smart connection pooling with these features:

- **Dynamic Pool Sizing** - Scales connections based on load with configurable min/max size
- **Connection Validation** - Checks connection health before returning from pool
- **Automatic Retry** - Exponential backoff for transient failures
- **Metrics Collection** - Tracks connection usage and query performance
- **Transaction Management** - Ensures proper transaction handling for write operations
- **Resource Cleanup** - Graceful connection closure on service shutdown

### Vector Search Implementation

Vector search is implemented directly in the [`Neo4jConnector`](neo4j_connector.py:182) class using Neo4j 5.x's native vector index capabilities:

```python
def semantic_search(self, query_embedding, node_label, limit=10):
    """
    Perform vector similarity search using the provided embedding.
    
    Args:
        query_embedding: The vector embedding to search against
        node_label: The node label to search within
        limit: Maximum number of results
        
    Returns:
        List of nodes with similarity scores
    """
    cypher = f"""
    MATCH (n:{node_label})
    WHERE n.embedding IS NOT NULL
    WITH n, gds.similarity.cosine(n.embedding, $embedding) AS score
    ORDER BY score DESC
    LIMIT $limit
    RETURN n, score
    """
    
    return self.execute_query(
        cypher,
        {"embedding": query_embedding, "limit": limit}
    )
```

### Error Handling Strategy

The connector implements a comprehensive error handling strategy:

- **Categorized Exceptions** - Custom exception hierarchy for different error types
- **Automatic Retries** - Configurable retry policy for transient failures
- **Detailed Logging** - Structured logging of all errors with context
- **Graceful Degradation** - Fallback mechanisms for non-critical failures
- **Circuit Breaking** - Protection against cascading failures during outages

Error hierarchy:

```python
class Neo4jError(Exception):
    """Base exception for all Neo4j-related errors."""
    
class ConnectionError(Neo4jError):
    """Error establishing connection to Neo4j."""
    
class QueryError(Neo4jError):
    """Error executing a Cypher query."""
    
class SchemaError(Neo4jError):
    """Error with graph schema operation."""
    
class TransactionError(Neo4jError):
    """Error in transaction management."""
```

## API Specifications

### Core Data Operations

#### Entity Management
```http
POST /api/v1/entities
  - Create new simulation entities with validation and relationship setup
  - Supports bulk creation for performance optimization
  - Returns entity ID and initial relationship mappings

GET /api/v1/entities/{id}
  - Retrieve entity details with configurable depth of related data
  - Supports projection queries to limit returned fields
  - Includes relationship metadata and traversal options

PUT /api/v1/entities/{id}
  - Update entity properties with conflict resolution
  - Maintains audit trail of changes
  - Supports partial updates and optimistic locking

DELETE /api/v1/entities/{id}
  - Soft delete with dependency checking
  - Cascade delete options for cleanup scenarios
  - Maintains referential integrity
```

#### Relationship Management
```http
POST /api/v1/relationships
  - Create typed relationships between entities
  - Supports relationship properties and metadata
  - Validates relationship constraints and business rules

GET /api/v1/relationships/{id}
  - Retrieve relationship details including source/target entities
  - Supports filtering by relationship type and properties

PUT /api/v1/relationships/{id}
  - Update relationship properties and metadata
  - Maintains relationship history for audit purposes

DELETE /api/v1/relationships/{id}
  - Remove relationships with impact analysis
  - Supports cascade operations based on business rules
```

#### Advanced Query Operations
```http
POST /api/v1/query/cypher
  - Execute custom Cypher queries with parameterization
  - Includes query optimization and execution plan analysis
  - Supports read-only and read-write operations with appropriate permissions

POST /api/v1/query/graph-pattern
  - Pattern-based graph traversal for complex scenarios
  - Template-based queries for common use cases
  - Performance optimized with caching and indexing

GET /api/v1/query/neighborhood/{nodeId}
  - Explore entity neighborhoods with configurable depth
  - Supports filtering and relationship type selection
  - Optimized for interactive graph exploration

POST /api/v1/query/path-analysis
  - Find paths between entities with constraints
  - Shortest path, all paths, and weighted path algorithms
  - Critical for dependency analysis and impact assessment

POST /api/v1/analytics/graph-algorithms
  - Execute graph algorithms (centrality, community detection, etc.)
  - Support for custom algorithm parameters
  - Results caching for expensive operations
```

### Simulation-Specific Operations

#### Simulation Lifecycle Management
```http
POST /api/v1/simulations
  - Create new simulation instances with complete metadata
  - Initialize simulation state and dependency graphs
  - Set up monitoring and audit frameworks

GET /api/v1/simulations/{simulationId}
  - Retrieve simulation details with current state
  - Includes performance metrics and execution timeline
  - Supports real-time status updates

PUT /api/v1/simulations/{simulationId}/state
  - Update simulation state with transaction support
  - Maintains state history for rollback capabilities
  - Triggers event notifications via service bus

DELETE /api/v1/simulations/{simulationId}
  - Clean simulation removal with data archival
  - Cascade delete of related simulation data
  - Maintains audit trail for compliance
```

#### Historical Data and Analytics
```http
GET /api/v1/history/simulations
  - Query simulation execution history with filtering
  - Supports time-range queries and pagination
  - Includes performance analytics and trends

GET /api/v1/history/entities/{entityId}
  - Retrieve entity change history and evolution
  - Point-in-time queries for specific states
  - Includes relationship change tracking

GET /api/v1/history/snapshots/{timestamp}
  - Retrieve complete simulation state at specific time
  - Supports comparative analysis between snapshots
  - Optimized for large dataset retrieval

POST /api/v1/analytics/trends
  - Analyze simulation patterns and trends
  - Machine learning insights on simulation performance
  - Predictive analytics for resource utilization
```

### Real-time Operations
```http
GET /api/v1/stream/simulation/{simulationId}
  - WebSocket endpoint for real-time simulation updates
  - Supports filtered event streams
  - Optimized for dashboard and monitoring integration

POST /api/v1/events/webhook
  - Register webhooks for simulation events
  - Supports custom event filtering and transformation
  - Integration with external monitoring systems
```

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
POST /tenant-discovery/import - Import TenantDiscoveryExport JSON data
```

### Neo4j Integration Endpoints
```
Bolt Protocol: bolt://localhost:7687 - Direct Neo4j access for agent connections
HTTP API: http://localhost:7474 - Neo4j browser and HTTP queries
Cypher Schema Conventions:
  - Resource nodes use Azure resource type as primary label (e.g., :VirtualMachine, :StorageAccount)
  - Tenant hierarchy maintained through :CONTAINS relationships
  - Resource dependencies expressed via :DEPENDS_ON relationships
  - Batch ingestion via LOAD CSV WITH HEADERS for large tenant exports (10,000+ resources)
```

## Dependencies

### Internal Dependencies
- **Azure Service Bus**: For receiving state update messages from agents and event-driven updates
- **Core API Service**: Authentication and authorization validation
- **Spec Library**: For schema validation and entity definitions

### External Dependencies
- **Neo4j Database**: Core graph database engine (v5.x) with APOC and vector search extensions
- **Redis**: Caching layer for query result caching and session management
- **Azure Key Vault**: Secure credential storage with automatic rotation
- **Azure Monitor**: Logging and metrics collection with custom dashboards
- **Entra ID**: Authentication and authorization with group-based access control
- **Docker/Podman**: For containerized deployment
- **Azure Storage**: For backup and disaster recovery
- **Tenant Discovery Agent**: Producer of Azure tenant resource graphs (compatible with v1.0+ exports)

### Operational Dependencies
- **Kubernetes**: Container orchestration with auto-scaling and health checks
- **Helm**: Package management for deployment configurations
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization and alerting dashboards

### Design Decisions

- **Multi-tenancy partitioning not required**: All tenant resource nodes share the same Neo4j database; isolation handled by application context

## Docker Configuration

The Neo4j database runs in a Docker container with the following configuration:

```yaml
neo4j:
  image: neo4j:5.11
  ports:
    - "7474:7474"  # HTTP for browser access
    - "7687:7687"  # Bolt protocol
  environment:
    - NEO4J_AUTH=neo4j/password  # Default credentials
    - NEO4J_apoc_export_file_enabled=true
    - NEO4J_apoc_import_file_enabled=true
    - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
    - NEO4J_dbms_memory_heap_initial__size=1G
    - NEO4J_dbms_memory_heap_max__size=2G
  volumes:
    - neo4j_data:/data  # Persistent data
    - ./plugins:/plugins  # Custom plugins
  healthcheck:
    test: ["CMD", "wget", "-q", "-O", "-", "http://localhost:7474"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Usage Examples

### Basic Query Execution

```python
from codestory.graphdb import Neo4jConnector

# Using context manager for automatic resource cleanup
with Neo4jConnector() as connector:
    # Simple query
    result = connector.execute_query(
        "MATCH (f:File) WHERE f.path CONTAINS $keyword RETURN f.path",
        {"keyword": "README"}
    )
    
    # Print results
    for record in result:
        print(record["f.path"])
```

### Transaction Management

```python
# Multiple operations in a single transaction
def create_class_hierarchy(connector, base_class, derived_classes):
    queries = []
    params_list = []
    
    # Create base class
    queries.append("CREATE (c:Class {name: $name, module: $module})")
    params_list.append({"name": base_class["name"], "module": base_class["module"]})
    
    # Create derived classes with inheritance relationships
    for derived in derived_classes:
        queries.append("""
        MATCH (base:Class {name: $base_name, module: $base_module})
        CREATE (derived:Class {name: $derived_name, module: $derived_module})
        CREATE (derived)-[:INHERITS_FROM]->(base)
        """)
        params_list.append({
            "base_name": base_class["name"],
            "base_module": base_class["module"],
            "derived_name": derived["name"],
            "derived_module": derived["module"]
        })
    
    # Execute all in one transaction
    connector.execute_many(queries, params_list, write=True)
```

### Async Usage with FastAPI

```python
from fastapi import FastAPI, Depends
from codestory.graphdb import Neo4jConnector

app = FastAPI()
connector = Neo4jConnector()

@app.on_event("shutdown")
async def shutdown():
    await connector.close_async()

@app.get("/files/{path}")
async def get_file_info(path: str):
    query = "MATCH (f:File {path: $path}) RETURN f"
    result = await connector.execute_query_async(query, {"path": path})
    
    if not result:
        return {"error": "File not found"}
    
    return {"file": dict(result[0]["f"])}
```

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
DISCOVERED_IN: Links resources to their source tenant discovery session
```

### TenantDiscoveryExport Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "tenantId": {
      "type": "string",
      "description": "Azure tenant identifier"
    },
    "discoveryTimestamp": {
      "type": "string",
      "format": "date-time"
    },
    "resources": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "type": {"type": "string"},
          "name": {"type": "string"},
          "location": {"type": "string"},
          "resourceGroup": {"type": "string"},
          "properties": {"type": "object"},
          "tags": {"type": "object"}
        },
        "required": ["id", "type", "name"]
      }
    },
    "relationships": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sourceId": {"type": "string"},
          "targetId": {"type": "string"},
          "type": {"type": "string"},
          "properties": {"type": "object"}
        },
        "required": ["sourceId", "targetId", "type"]
      }
    }
  },
  "required": ["tenantId", "resources", "relationships"]
}
```

### Constraints and Indexes

```cypher
// Unique constraints
CREATE CONSTRAINT IF NOT EXISTS ON (s:Simulation) ASSERT s.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS ON (a:AttackPattern) ASSERT a.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS ON (r:AzureResource) ASSERT r.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS ON (i:Identity) ASSERT i.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS ON (t:TelemetryPoint) ASSERT t.id IS UNIQUE;

// Full-text indexes
CREATE FULLTEXT INDEX resource_content IF NOT EXISTS FOR (r:AzureResource) ON EACH [r.name, r.type];
CREATE FULLTEXT INDEX simulation_name IF NOT EXISTS FOR (s:Simulation) ON EACH [s.name, s.description];

// Vector indexes (for semantic search)
CREATE VECTOR INDEX summary_embedding IF NOT EXISTS FOR (s:Summary)
ON s.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: "cosine"
}};

CREATE VECTOR INDEX documentation_embedding IF NOT EXISTS FOR (d:Documentation)
ON d.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: "cosine"
}};

// Performance indexes
CREATE INDEX IF NOT EXISTS FOR (r:AzureResource) ON (r.type);
CREATE INDEX IF NOT EXISTS FOR (r:AzureResource) ON (r.region);
CREATE INDEX IF NOT EXISTS FOR (s:Simulation) ON (s.status);
CREATE INDEX IF NOT EXISTS FOR (s:Simulation) ON (s.created_at);
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
- Test [`Neo4jConnector`](neo4j_connector.py:1) methods with mocked driver
- Test error handling and retry logic
- Test vector search functionality
- Test async connector operations
- Neo4j connection management and failover
- CRUD operations for all node and relationship types
- Cypher query builder and parameter binding
- Data validation and constraint enforcement
- Backup and restore functionality
- Performance benchmarks for common query patterns

### Integration Tests
- Use Neo4j Testcontainers to spin up actual database
- Test schema initialization
- Test data persistence between connections
- Test connection pooling behavior under load
- Test vector index creation and search
- **Live Neo4j instance required** - no mocking of database layer
- End-to-end simulation lifecycle with real graph operations
- Service Bus integration for state updates from agents
- Concurrent access patterns with multiple agent connections
- Large graph performance with 1000+ node simulations
- Disaster recovery with actual backup/restore cycles
- **Tenant Discovery Agent integration**: Run Tenant Discovery Agent on sample tenant, upload export via POST /tenant-discovery/import, assert node/edge count matches expected values
- Batch import performance testing with large tenant exports (10,000+ resources)

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
- **Tenant Discovery Integration**: Ingest 10,000-resource tenant export in under 5 minutes with zero errors

## Open Questions

### Technical Decisions
- What is the optimal indexing strategy for frequent relationship traversals?
- How should we handle schema evolution and migration for existing simulations?
- Should we implement read replicas for visualization queries vs. transactional operations?
- What backup retention policy aligns with simulation lifecycle requirements?
- How do we handle concurrent modifications to the same simulation graph?
- **Graph Database Choice**: Neo4j vs. Amazon Neptune vs. Azure Cosmos DB (Gremlin API) - evaluate based on specific query patterns and scale requirements?
- **Caching Strategy**: What specific caching patterns, TTL configurations, and cache invalidation strategies for different query types?
- **Query Optimization**: Indexing strategies for large-scale graph traversals and analytical workloads?

### Integration Patterns
- **Event Sourcing**: Should we implement event sourcing for graph state changes to enable audit trails and replay capabilities?
- **Data Synchronization**: How to handle real-time updates from multiple sources with conflict resolution?
- **Conflict Resolution**: Strategies for handling concurrent updates to the same entities with merge algorithms?
- **Schema Evolution**: How to handle schema changes and migrations without downtime?

### Performance Optimization
- **Query Caching**: Which queries should be cached, for how long, and what invalidation strategies?
- **Memory Management**: Optimal memory allocation for graph operations and garbage collection tuning?
- **Connection Pooling**: Optimal connection pool sizing and management strategies?
- **Partitioning Strategy**: How to partition large graphs across multiple nodes for optimal performance?

### Operational Concerns
- **Monitoring**: What specific metrics, alerts, and SLAs are most critical for graph operations?
- **Disaster Recovery**: RTO and RPO requirements for the graph database with geographic considerations?
- **Data Migration**: Strategies for schema evolution, data migration, and zero-downtime deployments?
- **Capacity Planning**: How to predict and plan for storage and compute capacity growth?

## Source Alignment Note

This specification was initially derived from the code-story project's Graph Database specification and adapted for SimBuilder's specific requirements. Key adaptations include:

- Integration with SimBuilder's service bus architecture
- Simulation-specific data models and operations
- Multi-tenant considerations for simulation isolation
- Performance requirements tailored to simulation workloads
- Security integration with SimBuilder's authentication system

The specification has been updated with enhanced external content while preserving SimBuilder-specific schema definitions and architectural considerations.

*Last synchronized with external source: 2025-06-05 (second merge) - updated with external changes including enhanced performance requirements, comprehensive API specifications with HTTP endpoints, expanded technical stack details with Java 21/Spring Boot 3.2+, comprehensive non-functional requirements with security and compliance standards, and detailed operational excellence practices*