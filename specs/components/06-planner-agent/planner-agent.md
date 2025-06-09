# Planner Agent Specification

## Purpose / Overview

The Planner Agent transforms structured attack specifications into concrete Azure resource plans with detailed dependency graphs, cost estimates, and deployment strategies. Using Microsoft's Autogen Core framework and Azure OpenAI, it leverages deep Azure expertise to design optimal cloud architectures that support attack scenarios while maintaining security, scalability, and cost efficiency. The agent serves as the architectural brain that bridges attack requirements to deployable infrastructure.

## Functional Requirements / User Stories

- As an **InfraSynthesis Agent**, I need detailed resource plans with explicit dependencies for IaC generation
- As a **Security Researcher**, I need cost-effective infrastructure that accurately simulates production environments
- As a **FinOps Team**, I need upfront cost estimates and budget compliance validation for all planned resources
- As an **Orchestrator Agent**, I need deployment ordering and dependency resolution strategies
- As a **Compliance Officer**, I need assurance that planned resources meet security and regulatory requirements
- As a **System Administrator**, I need resource plans that include monitoring, logging, and operational considerations

## Interfaces / APIs

### Inputs
- **Attack Specifications**: Complete attack specs from Clarifier Agent with all requirements
- **Budget Constraints**: Maximum spend limits, cost optimization preferences, and billing requirements
- **Compliance Requirements**: Security policies, data residency, and regulatory constraints
- **Template Library**: Reference architectures and proven resource patterns
- **Azure Service Catalog**: Current service availability, pricing, and regional capabilities

### Outputs
- **Resource Plans**: Detailed infrastructure specifications with dependencies and configurations
- **Cost Estimates**: Comprehensive cost breakdowns with optimization recommendations
- **Deployment Strategies**: Sequencing, rollback plans, and risk mitigation approaches
- **Compliance Reports**: Security validation and regulatory adherence documentation
- **Architecture Diagrams**: Visual representations of planned infrastructure topology

### Public REST / gRPC / CLI commands
```
POST /planner/plans - Create resource plan from attack specification
GET /planner/plans/{id} - Retrieve complete resource plan
PUT /planner/plans/{id}/optimize - Apply cost or performance optimizations
GET /planner/plans/{id}/costs - Get detailed cost breakdown and projections
GET /planner/plans/{id}/dependencies - Get dependency graph and deployment order
POST /planner/plans/{id}/validate - Validate plan against constraints and policies
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: GPT-4 for architectural reasoning and resource optimization
- **Clarifier Agent**: Attack specifications as primary input
- **Graph Database Service**: Storing resource plans and dependency relationships
- **Service Bus**: Publishing planning progress and completion events
- **Spec Library**: Access to template library and reference architectures
- **Azure Cost Management API**: Real-time pricing and cost estimation
- **Azure Resource Graph**: Service availability and regional capability queries
- **Liquid Template Engine**: Runtime loading of prompts from `prompts/planner/*.liquid` files
- **Prompt Templates**: External Liquid templates for resource analysis, plan generation, and cost estimation (no hard-coded prompts allowed)

## Data Contracts / Schemas

### Resource Planning Data
```python
class ResourcePlan(BaseModel):
    plan_id: str
    attack_spec_id: str
    plan_version: str
    created_at: datetime
    total_estimated_cost: CostEstimate
    deployment_strategy: DeploymentStrategy
    resource_groups: List[ResourceGroup]
    dependencies: DependencyGraph
    compliance_status: ComplianceReport

class ResourceGroup(BaseModel):
    name: str
    region: str
    purpose: str
    resources: List[AzureResource]
    estimated_cost: CostEstimate
    deployment_order: int

class AzureResource(BaseModel):
    resource_id: str
    resource_type: str
    name: str
    configuration: Dict[str, Any]
    dependencies: List[str]
    estimated_monthly_cost: float
    security_configuration: SecurityConfig
    monitoring_requirements: MonitoringConfig

class DependencyGraph(BaseModel):
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    deployment_phases: List[DeploymentPhase]
    critical_path: List[str]

class CostEstimate(BaseModel):
    monthly_estimate: float
    daily_estimate: float
    hourly_estimate: float
    breakdown_by_service: Dict[str, float]
    optimization_opportunities: List[CostOptimization]
```

### Planning Configuration
```python
class PlannerConfig(BaseModel):
    cost_optimization_level: CostOptimizationLevel
    security_baseline: SecurityBaseline
    performance_requirements: PerformanceRequirements
    regional_preferences: List[str]
    service_preferences: Dict[str, Any]
    compliance_frameworks: List[str]

class CostOptimizationLevel(str, Enum):
    AGGRESSIVE = "aggressive"  # Minimal viable resources
    BALANCED = "balanced"     # Cost-performance balance
    PREMIUM = "premium"       # Performance over cost
```

## Documentation to Produce

- **Azure Service Selection Guide**: How the agent chooses optimal services for attack scenarios
- **Cost Optimization Strategies**: Techniques for balancing cost, performance, and security
- **Dependency Resolution Algorithms**: How complex resource dependencies are managed
- **Compliance Validation Procedures**: Ensuring plans meet security and regulatory requirements
- **Liquid Template Documentation**: Template variable definitions and usage patterns for `prompts/planner/*.liquid` files
- **Prompt Template Guidelines**: Standards for creating, testing, and maintaining external Liquid prompt templates
- **Template Variable Schema**: Complete specification of all variables used across planner prompt templates
- **Performance Tuning Guide**: Optimizing plan generation speed and quality

## Testing Strategy

### Unit Tests
- Resource dependency calculation and cycle detection
- Cost estimation accuracy and edge case handling
- Compliance validation rule engine
- Template matching and customization logic
- Azure service configuration generation
- Plan optimization algorithms
- Liquid template loading and variable validation
- Template rendering with various resource plan scenarios
- Prompt template syntax validation and error handling

### Integration Tests
- **Live Azure services required** - no mocking of Azure APIs for cost and service data
- End-to-end planning from attack specifications to deployable plans
- Cost estimation validation against actual Azure pricing
- Compliance framework integration and policy validation
- Template library integration and pattern matching
- Complex dependency resolution with multi-region deployments
- External Liquid template loading from `prompts/planner/` directory
- Template variable injection and rendering accuracy

### Acceptance Tests
- Complete resource plans for representative attack scenarios
- Cost accuracy validation within 10% of actual deployment costs
- Deployment success rates following generated plans and dependencies
- Compliance validation against enterprise security policies
- Performance benchmarks for plan generation under various complexity levels
- Prompt template lint validation in CI/CD pipeline
- Template variable completeness and consistency across all planner prompts

## Acceptance Criteria

- **Accuracy**: Generate deployable plans with 95%+ success rate for typical attack scenarios
- **Cost Precision**: Cost estimates within 15% of actual Azure billing for deployed resources
- **Performance**: Generate complete resource plans within 30 seconds for complex scenarios
- **Compliance**: 100% adherence to specified security and regulatory requirements
- **Optimization**: Identify cost savings opportunities averaging 20%+ from baseline configurations
- **Dependencies**: Generate deployment orders that prevent dependency conflicts
- **Scalability**: Handle plans with 100+ resources across multiple regions and subscriptions
- **Template Compliance**: All prompts MUST be loaded from external Liquid templates in `prompts/planner/` directory
- **Template Quality**: All Liquid templates MUST pass CI/CD linting with valid syntax and complete variable definitions
- **Runtime Loading**: Template loading failures MUST cause graceful agent initialization failure with clear error messages

## Open Questions

- How should we handle cost optimization when attack fidelity requires specific expensive resources?
- What approach should we use for multi-cloud scenarios or hybrid Azure/on-premises deployments?
- Should we implement machine learning for improving plan quality based on deployment outcomes?
- How do we handle resource quota limitations and subscription constraints in planning?
- What strategy should we use for handling Azure service deprecations and regional limitations?
- Should we implement collaborative planning workflows for complex multi-team scenarios?
- How do we balance infrastructure realism with cost efficiency for simulation environments?
- What mechanisms should we provide for manual plan adjustments and override capabilities?