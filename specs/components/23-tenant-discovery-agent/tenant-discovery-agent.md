# Tenant Discovery Agent Specification

## Purpose / Overview

The Tenant Discovery Agent performs comprehensive enumeration of Azure tenant resources using both Azure Resource Manager (ARM) APIs and Azure Resource Graph queries. It systematically discovers all resources, relationships, configurations, and metadata within a target Azure tenant, then populates the Neo4j Graph Database with the complete resource topology. Additionally, it generates detailed narrative documentation sufficient to reproduce the tenant architecture, enabling accurate simulation environment creation based on real-world production environments.

## Functional Requirements / User Stories

- As a **Security Researcher**, I need to discover all resources in a target Azure tenant to understand the complete attack surface and environment topology
- As a **Red Team Member**, I need comprehensive tenant enumeration to identify potential attack paths and vulnerable configurations across all Azure services
- As a **SimBuilder System**, I need detailed tenant resource graphs stored in Neo4j to enable accurate environment replication and simulation planning
- As a **Infrastructure Analyst**, I need narrative documentation of discovered tenant architecture to understand dependencies, configurations, and relationships
- As a **Compliance Auditor**, I need complete visibility into tenant resources, permissions, and configurations for security assessments
- As a **Core API Service**, I need real-time progress updates on discovery operations and completion notifications for downstream processing
- As a **System Administrator**, I need discovery operations to respect rate limits and handle API throttling gracefully
- As a **Data Engineer**, I need standardized resource metadata and relationship modeling for consistent graph database population

## Interfaces / APIs

### Inputs
- **Azure Tenant Credentials**: Service principal, managed identity, or user credentials with appropriate read permissions
- **Discovery Scope Configuration**: Resource groups, subscriptions, or tenant-wide discovery parameters
- **Rate Limiting Settings**: API throttling configurations and concurrent request limits
- **Filter Criteria**: Resource types, regions, tags, or naming patterns to include/exclude
- **Output Format Preferences**: Narrative documentation format (Markdown, JSON, YAML) and detail levels

### Outputs
- **Neo4j Resource Graph**: Complete tenant topology with resources, relationships, and metadata
- **Narrative Documentation**: Human-readable tenant architecture description with reproduction instructions
- **Discovery Metadata**: Enumeration statistics, discovered resource counts, and operation summary
- **Resource Inventory**: Structured catalog of all discovered resources with configurations
- **Progress Updates**: Real-time discovery status via Service Bus messaging
- **Error Reports**: Failed discoveries, permission issues, and API limitations encountered

### Public REST / gRPC / CLI commands
```http
POST /tenant-discovery/sessions
  - Start new tenant discovery session with scope and credentials
  - Request: {"tenant_id": "uuid", "scope": DiscoveryScope, "credentials": AzureCredentials}
  - Response: {"session_id": "uuid", "status": "initializing", "estimated_duration": "PT30M"}
  - Consumer: Core API Service, CLI Interface

GET /tenant-discovery/sessions/{id}/status
  - Get current discovery progress and metrics
  - Response: {"status": "discovering_resources", "progress": 65, "resources_found": 1247, "eta": "PT15M"}
  - Consumer: Core API Service, GUI Interface, Progress Monitoring

POST /tenant-discovery/sessions/{id}/pause
  - Pause ongoing discovery operation with state preservation
  - Request: {"reason": "rate_limit_hit"}
  - Response: {"status": "paused", "resume_token": "abc123", "resources_discovered": 892}
  - Consumer: Rate Limiting Systems, Manual Controls

POST /tenant-discovery/sessions/{id}/resume
  - Resume paused discovery operation from saved state
  - Request: {"resume_token": "abc123"}
  - Response: {"status": "discovering_resources", "resumed_from": "subscription_enumeration"}
  - Consumer: Rate Limiting Systems, Manual Controls

DELETE /tenant-discovery/sessions/{id}
  - Cancel discovery session and cleanup partial data
  - Response: {"status": "cancelled", "partial_results_available": true, "cleanup_job_id": "uuid"}
  - Consumer: Emergency Controls, Session Management

GET /tenant-discovery/sessions/{id}/results
  - Retrieve complete discovery results and export data
  - Response: TenantDiscoveryExport with resources and relationships
  - Consumer: Graph Database Service, Core API Service, Data Analysis

GET /tenant-discovery/sessions/{id}/narrative
  - Get generated narrative documentation in specified format
  - Query params: format (markdown, json, html), detail_level (summary, detailed, comprehensive)
  - Response: NarrativeDocumentation with architecture description
  - Consumer: Documentation Systems, Reporting, Human Review

POST /tenant-discovery/validate-credentials
  - Validate Azure credentials and enumerate accessible permissions
  - Request: AzureCredentials
  - Response: {"valid": true, "permissions": [...], "accessible_subscriptions": [...]}
  - Consumer: Credential Management, Pre-flight Validation

GET /tenant-discovery/sessions/{id}/export
  - Export discovery results in various formats
  - Query params: format (json, csv, cypher), include_relationships (boolean)
  - Response: Formatted export data for external consumption
  - Consumer: Data Integration, External Systems, Backup
```

### Azure Integration Interface
```python
class AzureDiscoveryClient:
    """Azure API integration for comprehensive tenant discovery."""
    
    def authenticate(self, credentials: AzureCredentials) -> bool:
        """Authenticate with Azure using provided credentials."""
        
    def enumerate_subscriptions(self) -> List[AzureSubscription]:
        """Discover all accessible subscriptions in tenant."""
        
    def discover_resources(self, subscription_id: str, resource_types: List[str] = None) -> List[AzureResource]:
        """Enumerate resources within subscription using ARM and Resource Graph."""
        
    def analyze_relationships(self, resources: List[AzureResource]) -> List[ResourceRelationship]:
        """Analyze and map relationships between discovered resources."""
        
    def validate_permissions(self, subscription_id: str) -> PermissionReport:
        """Validate current permissions and identify access limitations."""
```

### Progress Notification Interface
```python
class DiscoveryProgressNotifier:
    """Real-time progress updates via Service Bus."""
    
    def notify_session_started(self, session_id: str, scope: DiscoveryScope) -> None:
        """Notify that discovery session has started."""
        
    def notify_progress_update(self, session_id: str, progress: DiscoveryProgress) -> None:
        """Send progress update with current metrics."""
        
    def notify_session_completed(self, session_id: str, results: TenantDiscoveryExport) -> None:
        """Notify that discovery has completed with results summary."""
        
    def notify_error(self, session_id: str, error: DiscoveryError) -> None:
        """Report discovery errors and failures."""
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: For intelligent narrative generation and enumeration analysis
- **Azure Resource Manager (ARM) APIs**: Complete resource enumeration and configuration retrieval
- **Azure Resource Graph**: Cross-subscription resource queries and relationship discovery
- **Microsoft Graph API**: Azure AD, identity, and permission enumeration
- **Graph Database Service**: Neo4j storage for discovered resource topology and relationships
- **Core API Service**: Session management, authentication, and operation coordination
- **Service Bus**: Progress notifications and workflow event publishing
- **Azure Identity Libraries**: Authentication and credential management for Azure APIs
- **Rate Limiting Service**: API throttling and concurrent request management
- **Liquid Template Engine**: Runtime loading of prompts from `prompts/tenant-discovery/*.liquid` files
- **Prompt Templates**: External Liquid templates for enumeration analysis, graph population, and narrative generation (no hard-coded prompts allowed)

## Data Contracts / Schemas

### Discovery Session Data
```python
class TenantDiscoverySession(BaseModel):
    session_id: str
    tenant_id: str
    subscription_ids: List[str]
    discovery_scope: DiscoveryScope
    credentials: AzureCredentials
    discovery_status: DiscoveryStatus
    progress_metrics: DiscoveryProgress
    discovered_resources: List[AzureResource]
    resource_relationships: List[ResourceRelationship]
    narrative_output: Optional[NarrativeDocumentation]
    error_log: List[DiscoveryError]

class DiscoveryScope(BaseModel):
    scope_type: ScopeType  # TENANT, SUBSCRIPTION, RESOURCE_GROUP
    target_ids: List[str]
    resource_types: Optional[List[str]]
    regions: Optional[List[str]]
    tag_filters: Optional[Dict[str, str]]
    exclude_patterns: Optional[List[str]]

class DiscoveryStatus(str, Enum):
    INITIALIZING = "initializing"
    DISCOVERING_SUBSCRIPTIONS = "discovering_subscriptions"
    DISCOVERING_RESOURCES = "discovering_resources"
    DISCOVERING_RELATIONSHIPS = "discovering_relationships"
    POPULATING_GRAPH = "populating_graph"
    GENERATING_NARRATIVE = "generating_narrative"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class AzureResource(BaseModel):
    resource_id: str
    resource_type: str
    resource_name: str
    subscription_id: str
    resource_group: str
    location: str
    tags: Dict[str, str]
    properties: Dict[str, Any]
    identity: Optional[ResourceIdentity]
    sku: Optional[ResourceSku]
    dependencies: List[str]
    created_time: Optional[datetime]
    modified_time: Optional[datetime]

class ResourceRelationship(BaseModel):
    source_resource_id: str
    target_resource_id: str
    relationship_type: RelationshipType
    relationship_properties: Dict[str, Any]

class RelationshipType(str, Enum):
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"
    NETWORK_CONNECTED = "network_connected"
    IDENTITY_ACCESS = "identity_access"
    DATA_FLOW = "data_flow"
    POLICY_APPLIED = "policy_applied"
    MANAGED_BY = "managed_by"

class NarrativeDocumentation(BaseModel):
    tenant_overview: str
    resource_summary: ResourceSummary
    architecture_description: str
    network_topology: str
    identity_structure: str
    security_configuration: str
    reproduction_instructions: str
    dependencies_analysis: str
    cost_estimation: Optional[str]
```

### Discovery Configuration
```python
class TenantDiscoveryConfig(BaseModel):
    max_concurrent_requests: int = 10
    api_retry_attempts: int = 3
    rate_limit_delay_seconds: float = 1.0
    discovery_timeout_minutes: int = 60
    graph_batch_size: int = 100
    narrative_detail_level: NarrativeDetailLevel = NarrativeDetailLevel.DETAILED
    include_sensitive_data: bool = False
    export_formats: List[ExportFormat] = [ExportFormat.MARKDOWN, ExportFormat.JSON]

class NarrativeDetailLevel(str, Enum):
    SUMMARY = "summary"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"
```

## Documentation to Produce

- **Azure API Integration Guide**: ARM, Resource Graph, and Microsoft Graph API usage patterns
- **Resource Discovery Strategies**: Systematic enumeration approaches and optimization techniques
- **Graph Database Schema**: Neo4j node types, relationships, and indexing strategies for Azure resources
- **Narrative Generation Framework**: Template-based documentation generation with customizable detail levels
- **Rate Limiting and Throttling**: Best practices for Azure API consumption and error handling
- **Permission Requirements**: Minimum Azure RBAC permissions needed for comprehensive tenant discovery
- **Performance Optimization**: Concurrent processing, caching, and resource batching strategies
- **Error Handling Patterns**: Recovery strategies for API failures, permission issues, and timeout scenarios
- **Liquid Template Documentation**: Template variable definitions and usage patterns for `prompts/tenant-discovery/*.liquid` files
- **Prompt Template Guidelines**: Standards for creating, testing, and maintaining external Liquid prompt templates
- **Template Variable Schema**: Complete specification of all variables used across tenant-discovery prompt templates

## Testing Strategy

### Unit Tests
- Azure API client initialization and authentication
- Resource enumeration logic and filtering
- Graph database population and relationship creation
- Narrative documentation generation
- Rate limiting and throttling mechanisms
- Error handling and retry logic
- Data transformation and schema mapping
- Liquid template loading and variable validation
- Template rendering with various tenant discovery scenarios
- Prompt template syntax validation and error handling

### Integration Tests
- **Live Azure tenant required** - no mocking of Azure services
- End-to-end tenant discovery with real Azure resources
- Neo4j graph population with actual resource data
- Multi-subscription discovery scenarios
- Large-scale tenant enumeration performance testing
- API rate limiting and throttling behavior validation
- Cross-service relationship discovery accuracy
- External Liquid template loading from `prompts/tenant-discovery/` directory
- Template variable injection and rendering accuracy

### Acceptance Tests
- Complete tenant discovery and graph population for real production-like environments
- Narrative documentation quality and reproduction accuracy assessment
- Performance benchmarks for various tenant sizes and complexity levels
- Permission boundary testing with limited credential scenarios
- Concurrent discovery session handling and resource contention
- Data consistency validation between discovered resources and graph storage
- Prompt template lint validation in CI/CD pipeline
- Template variable completeness and consistency across all tenant-discovery prompts

## Acceptance Criteria

- **Completeness**: Discover 99%+ of accessible Azure resources within scope and permission boundaries
- **Accuracy**: Maintain data fidelity with 100% accuracy for resource properties and relationships
- **Performance**: Complete tenant discovery within 30 minutes for typical enterprise tenants (1000+ resources)
- **Reliability**: Handle API throttling gracefully with automatic retry and backoff mechanisms
- **Scalability**: Support concurrent discovery of multiple tenants without resource conflicts
- **Documentation Quality**: Generate narrative documentation sufficient for 90%+ reproduction accuracy
- **Graph Integrity**: Ensure Neo4j graph consistency with proper indexing and relationship validation
- **Security**: Respect Azure RBAC permissions and never attempt unauthorized resource access
- **Template Compliance**: All prompts MUST be loaded from external Liquid templates in `prompts/tenant-discovery/` directory
- **Template Quality**: All Liquid templates MUST pass CI/CD linting with valid syntax and complete variable definitions
- **Runtime Loading**: Template loading failures MUST cause graceful agent initialization failure with clear error messages

## Open Questions

- How should we handle very large tenants (10,000+ resources) while maintaining reasonable discovery times?
- What level of configuration detail should we capture for complex resources like Azure Kubernetes Service?
- Should we implement incremental discovery to detect changes in previously discovered tenants?
- How do we balance narrative documentation detail with readability and usefulness?
- What approach should we use for discovering cross-tenant relationships in multi-tenant scenarios?
- Should we implement cost estimation capabilities based on discovered resource configurations?
- How do we handle Azure services with limited ARM/Resource Graph API support?
- What privacy and compliance considerations apply to storing detailed tenant resource information?
- Should we implement export capabilities for discovered data to other formats beyond Neo4j?
- How do we ensure discovered resource relationships remain current as Azure services evolve?