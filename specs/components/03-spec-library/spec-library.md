# Spec Library (Git Layer) Specification

## Purpose / Overview

The Spec Library provides version-controlled storage and management of simulation specifications, attack patterns, Infrastructure-as-Code templates, and deployment manifests. Built as a Git-based repository layer, it enables reproducible simulations, template sharing, collaborative specification development, and audit trails for all simulation artifacts. The library serves as the definitive source for simulation blueprints and enables simulation recreation from stored specifications.

## Functional Requirements / User Stories

- As a **Planner Agent**, I need to store and retrieve attack pattern templates and resource plans for reuse across simulations
- As an **InfraSynthesis Agent**, I need to store and version IaC templates (Bicep, Terraform, ARM) generated for different scenarios
- As a **Core API Service**, I need to manage simulation specifications with full version history and branching
- As a **Security Researcher**, I need to share and collaborate on attack scenario specifications across teams
- As a **Compliance Officer**, I need immutable audit trails of all simulation specifications and changes
- As a **Developer**, I need to recreate exact simulation environments from stored specifications
- As an **Operations Team**, I need to track specification lineage and impact analysis for changes

## Interfaces / APIs

### Inputs
- **Attack Specifications**: Structured YAML/JSON attack scenario definitions
- **Resource Plans**: Infrastructure resource definitions and dependency graphs
- **IaC Templates**: Bicep, Terraform, and ARM template files
- **Deployment Manifests**: Complete deployment configuration with parameters
- **Telemetry Schemas**: Monitoring and logging configuration specifications
- **Validation Scripts**: Environment validation and precondition checks

### Outputs
- **Specification Retrieval**: Versioned specifications by ID, tag, or branch
- **Template Libraries**: Categorized IaC templates and attack patterns
- **Diff Analysis**: Changes between specification versions
- **Dependency Maps**: Specification relationships and impact analysis
- **Audit Reports**: Change history and authorship tracking

### Public REST / gRPC / CLI commands
```http
POST /specs/simulations
  - Create new simulation specification with Git commit
  - Request: SimulationSpec with metadata and attack scenario
  - Response: {"spec_id": "uuid", "version": "v1.0.0", "commit_hash": "abc123"}
  - Consumer: Core API Service, CLI Interface

PUT /specs/simulations/{id}
  - Update simulation specification and create new version
  - Request: Updated SimulationSpec
  - Response: {"spec_id": "uuid", "version": "v1.1.0", "diff_summary": "Updated infrastructure section"}
  - Consumer: Core API Service, GUI Interface

GET /specs/simulations/{id}
  - Retrieve simulation specification by ID and optional version
  - Query params: version (defaults to latest)
  - Response: Complete SimulationSpec with metadata
  - Consumer: Planner Agent, InfraSynthesis Agent, Core API Service

GET /specs/simulations/{id}/versions
  - List all versions of a specification with change summary
  - Response: {"versions": [{"version": "v1.0.0", "created_at": "...", "changes": "Initial"}]}
  - Consumer: GUI Interface, Audit Systems

GET /specs/templates/attacks
  - List available attack pattern templates from library
  - Query params: category, severity, mitre_tactics
  - Response: {"templates": [AttackTemplate], "total": 45}
  - Consumer: Clarifier Agent, Core API Service, GUI Interface

GET /specs/templates/infrastructure
  - List IaC template library with categorization
  - Query params: provider, complexity, environment_type
  - Response: {"templates": [InfraTemplate], "categories": ["multi-tenant", "hybrid"]}
  - Consumer: Planner Agent, InfraSynthesis Agent

POST /specs/templates
  - Add new template to library with validation
  - Request: {"type": "attack|infrastructure", "template": TemplateSpec, "category": "string"}
  - Response: {"template_id": "uuid", "status": "validated", "library_path": "/templates/attacks/..."}
  - Consumer: Template Authors, Core API Service

GET /specs/audit/{simulation_id}
  - Get complete specification change history and lineage
  - Response: {"changes": [AuditEntry], "authors": [...], "merge_history": [...]}
  - Consumer: Compliance Systems, Operations Dashboard

POST /specs/simulations/{id}/fork
  - Create new specification based on existing one
  - Request: {"new_name": "string", "description": "string"}
  - Response: {"new_spec_id": "uuid", "source_version": "v1.2.0"}
  - Consumer: GUI Interface, Template Development

GET /specs/simulations/{id}/dependencies
  - Analyze specification dependencies and impact
  - Response: {"dependencies": [...], "dependent_specs": [...], "circular_refs": []}
  - Consumer: Impact Analysis, Validation Systems
```

### Git Repository Interface
```python
class SpecRepository:
    """Git-based specification repository management."""
    
    def create_specification(self, spec: SimulationSpec) -> SpecVersion:
        """Create new specification with initial Git commit."""
        
    def update_specification(self, spec_id: str, updated_spec: SimulationSpec) -> SpecVersion:
        """Update specification and create new version with Git commit."""
        
    def get_specification(self, spec_id: str, version: str = "latest") -> SimulationSpec:
        """Retrieve specification by ID and version from Git."""
        
    def list_versions(self, spec_id: str) -> List[SpecVersion]:
        """List all versions of a specification from Git history."""
        
    def create_branch(self, spec_id: str, branch_name: str) -> bool:
        """Create new branch for collaborative specification editing."""
        
    def merge_branch(self, spec_id: str, source_branch: str, target_branch: str) -> MergeResult:
        """Merge specification changes between branches."""
        
    def validate_specification(self, spec: SimulationSpec) -> ValidationResult:
        """Validate specification against schema and business rules."""
```

### Template Management Interface
```python
class TemplateLibrary:
    """Centralized template library management."""
    
### Consumer Components
The Spec Library provides interfaces consumed by:
- **Core API Service**: Template management via [`GET /specs/templates/attacks`](spec_repository.py:45) and specification storage
- **Clarifier Agent**: Attack pattern templates via [`TemplateLibrary.search_templates()`](template_library.py:23) and pattern matching
- **Planner Agent**: Infrastructure templates via [`GET /specs/templates/infrastructure`](spec_repository.py:67) and resource planning
- **InfraSynthesis Agent**: IaC template retrieval via [`TemplateLibrary.get_template()`](template_library.py:31) and manifest generation
- **Tenant Discovery Agent**: Specification creation via [`SpecRepository.create_specification()`](spec_repository.py:15) for discovered environments
- **GUI Interface**: Specification browsing via [`GET /specs/simulations/{id}/versions`](spec_repository.py:56) and collaborative editing
- **CLI Interface**: Template upload via [`POST /specs/templates`](spec_repository.py:78) and specification management
- **Operations Dashboard**: Audit tracking via [`GET /specs/audit/{simulation_id}`](spec_repository.py:89) and compliance reporting
    def add_attack_template(self, template: AttackTemplate) -> str:
        """Add new attack pattern template to library."""
        
    def add_infrastructure_template(self, template: InfraTemplate) -> str:
        """Add new infrastructure template to library."""
        
    def search_templates(self, criteria: SearchCriteria) -> List[Template]:
        """Search templates by category, complexity, provider, etc."""
        
    def get_template(self, template_id: str) -> Template:
        """Retrieve specific template by ID."""
        
    def validate_template(self, template: Template) -> ValidationResult:
        """Validate template syntax and completeness."""
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **Git Repository**: Primary version control system (Azure DevOps, GitHub, or GitLab)
- **Core API Service**: Authentication and access control integration
- **Graph Database Service**: Specification metadata and relationship storage
- **Azure Storage**: Large artifact storage and backup
- **CI/CD Pipeline**: Automated validation and template testing
- **Attack spec artifacts are not sensitive**: They are stored in plain text within the repository; standard Git access control applies.

## Data Contracts / Schemas

### Specification Structure
```yaml
SimulationSpec:
  metadata:
    id: string
    name: string
    version: semver
    created_by: string
    created_at: timestamp
    tags: array[string]
  
  attack_scenario:
    description: string
    mitre_tactics: array[string]
    target_environment: object
    preconditions: array[string]
  
  infrastructure:
    tenants: array[TenantSpec]
    networks: array[NetworkSpec]
    workloads: array[WorkloadSpec]
    identities: array[IdentitySpec]
  
  deployment:
    iac_provider: enum [terraform, bicep, arm]
    templates: array[TemplateReference]
    parameters: object
    dependencies: array[string]
  
  telemetry:
    collection_points: array[TelemetryPoint]
    expected_events: array[EventSchema]
    monitoring_config: object

AttackTemplate:
  metadata:
    name: string
    category: string
    severity: enum [low, medium, high, critical]
    mitre_techniques: array[string]
  
  specification:
    description: string
    requirements: object
    variations: array[object]
```

### Repository Structure
```
/specifications/
  /simulations/
    /{simulation-id}/
      spec.yaml
      versions/
        v1.0.0/
        v1.1.0/
  /templates/
    /attacks/
      lateral-movement/
      privilege-escalation/
      data-exfiltration/
    /infrastructure/
      multi-tenant/
      single-tenant/
      hybrid-cloud/
  /shared/
    /schemas/
    /validators/
```

## Documentation to Produce

- **Specification Schema Reference**: YAML/JSON schema documentation with examples
- **Template Development Guide**: Creating reusable attack and infrastructure templates
- **Version Control Workflow**: Branching, tagging, and release management procedures
- **API Integration Guide**: How services interact with the spec library
- **Template Library Catalog**: Organized catalog of available templates
- **Compliance and Audit Guide**: Audit trail management and compliance reporting

## Testing Strategy

### Unit Tests
- Git operations (clone, commit, push, pull, merge)
- Specification validation and schema compliance
- Template rendering and parameter substitution
- Version management and tagging
- Access control and permission validation
- File format parsing (YAML, JSON) and serialization

### Integration Tests
- **Live Git repository required** - no mocking of version control operations
- End-to-end specification storage and retrieval
- Template library management with real file operations
- Concurrent access and merge conflict resolution
- Large specification handling and performance
- CI/CD pipeline integration with actual template validation

### Acceptance Tests
- Complete simulation lifecycle with specification versioning
- Template sharing and reuse across multiple simulations
- Audit trail generation and compliance reporting
- Specification recreation and environment reproduction
- Collaborative editing with multiple users and branching

## Acceptance Criteria

- **Version Control**: Full Git history with branching, tagging, and merge capabilities
- **Performance**: Sub-second retrieval for specifications up to 100MB
- **Scalability**: Support 1000+ specifications with 10+ versions each
- **Security**: Role-based access control with encrypted storage
- **Reliability**: 99.9% availability with backup and disaster recovery
- **Compliance**: Immutable audit trails with digital signatures
- **Usability**: Intuitive API with comprehensive validation and error messages

## Open Questions

- Should we implement specification locking for concurrent editing scenarios?
- What branching strategy best supports collaborative specification development?
- How should we handle large binary artifacts (VM images, datasets) in specifications?
- Should we implement automatic specification validation pipelines on commit?
- What retention policy should we use for specification versions and history?
- How do we handle specification dependencies and circular references?
- Should we implement specification marketplace/sharing capabilities across organizations?
- What format should we use for specification encryption and digital signatures?