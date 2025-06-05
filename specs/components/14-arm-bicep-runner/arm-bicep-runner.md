# ARM/Bicep Runner Specification

## Purpose / Overview

The ARM/Bicep Runner component executes Azure Resource Manager (ARM) templates and Bicep infrastructure-as-code configurations for SimBuilder simulation environments. It provides native Azure deployment capabilities with advanced template management, parameter handling, deployment validation, and rollback mechanisms. This component specializes in Azure-native infrastructure deployment patterns and integrates deeply with Azure Resource Manager APIs for optimal performance and feature coverage.

## Functional Requirements / User Stories

- As an **Orchestrator Agent**, I need to deploy Azure infrastructure using ARM and Bicep templates with comprehensive parameter management
- As a **Planner Agent**, I need to validate ARM/Bicep templates and perform cost estimation before deployment
- As an **InfraSynthesis Agent**, I need to execute generated Bicep templates with proper dependency ordering and error handling
- As an **Operations Team**, I need reliable deployment monitoring with real-time progress tracking and detailed logging
- As a **Security Officer**, I need policy validation and compliance checking integrated into deployment workflows
- As a **Cost Manager**, I need accurate cost projections and budget enforcement during resource provisioning
- As a **Developer**, I need template debugging capabilities and detailed error diagnostics for failed deployments
- As a **Compliance Officer**, I need audit trails of all ARM deployments and resource group operations

## Interfaces / APIs

### Inputs
- **BicepSpec objects**: Bicep template configurations with parameters and deployment metadata
- **ARMTemplate objects**: ARM JSON templates with parameter files and deployment scope
- **DeploymentScope**: Resource group, subscription, or management group deployment targets
- **PolicyValidation**: Azure Policy compliance requirements and governance rules
- **RollbackRequests**: Instructions for resource cleanup and deployment cancellation

### Outputs
- **DeploymentResults**: Azure deployment status with resource details and outputs
- **ResourceGroups**: Created resource groups with metadata and resource inventories
- **PolicyCompliance**: Compliance validation results and policy violation reports
- **CostProjections**: Real-time cost estimates and resource utilization forecasts
- **TemplateValidation**: Template syntax and dependency validation results

### Public Endpoints / CLI Commands
```
POST /arm/validate - Validate ARM/Bicep template syntax and dependencies
POST /arm/deploy - Execute ARM/Bicep deployment
POST /arm/preview - Generate deployment preview with what-if analysis
GET /arm/status/{deployment_id} - Check deployment progress and status
POST /arm/cancel - Cancel in-progress deployment
DELETE /arm/cleanup/{resource_group} - Clean up resource group and dependencies
GET /arm/outputs/{deployment_id} - Retrieve deployment outputs and metadata
GET /arm/audit/{simulation_id} - Retrieve deployment audit logs
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings

- **Azure CLI**: For ARM template deployment and management operations
- **Bicep CLI**: For Bicep template compilation and validation
- **Azure Resource Manager APIs**: For direct deployment and resource management
- **Azure Policy**: For governance and compliance validation
- **Orchestrator Agent**: For deployment coordination and workflow integration
- **Core API Service**: For authentication and request processing
- **Graph Database Service**: For storing deployment metadata and resource relationships
- **FinOps Alerting**: For cost monitoring and budget enforcement
- **Azure Monitor**: For deployment telemetry and performance monitoring

## Data Contracts / Schemas

### BicepSpec Schema
```yaml
BicepSpec:
  template_name: string
  simulation_id: string
  deployment_scope:
    type: enum [ResourceGroup, Subscription, ManagementGroup]
    target_name: string
    location: string
  bicep_content:
    main_bicep: string # Base64 encoded Bicep template
    modules: array[BicepModule] # Referenced modules
    parameters_json: string # Parameter values
  compilation_options:
    target_scope: string
    no_restore: boolean
    stdout_to_file: boolean
  deployment_options:
    mode: enum [Incremental, Complete]
    confirm_with_what_if: boolean
    rollback_on_error: boolean
    timeout_minutes: integer

ARMTemplate:
  template_name: string
  simulation_id: string
  deployment_scope: DeploymentScope
  template_content:
    template_json: string # ARM template JSON
    parameters_json: string # Parameter file
    metadata: TemplateMetadata
  deployment_mode: enum [Incremental, Complete, Validate]
  dependency_chain: array[string] # Template dependencies
```

### Deployment Results Schema
```yaml
DeploymentResult:
  deployment_id: string
  deployment_name: string
  resource_group: string
  status: enum [Running, Succeeded, Failed, Canceled]
  provisioning_state: string
  correlation_id: string
  timestamp: datetime
  duration_minutes: integer
  deployed_resources:
    - resource_id: string
      resource_type: string
      resource_name: string
      provisioning_state: string
      location: string
      tags: object
  deployment_outputs: object
  error_details: array[DeploymentError]
  cost_estimate: CostProjection
  policy_compliance: ComplianceResult

PolicyValidationResult:
  compliant: boolean
  violations: array[PolicyViolation]
  exemptions: array[PolicyExemption]
  evaluation_details:
    policies_evaluated: integer
    violations_found: integer
    warnings_issued: integer
```

## Documentation to Produce

- **ARM/Bicep Architecture Guide**: Design patterns for Azure-native infrastructure deployment
- **Template Development Guide**: Best practices for Bicep and ARM template creation
- **Deployment Patterns Manual**: Common deployment scenarios and configuration examples
- **Policy Integration Guide**: Azure Policy compliance validation and enforcement
- **Performance Optimization Guide**: Template optimization and deployment acceleration strategies
- **Troubleshooting Runbook**: Common deployment failures and resolution procedures

## Testing Strategy

### Unit Tests
- Bicep template compilation and validation logic
- ARM template parameter processing and validation
- Deployment status monitoring and progress tracking
- Error handling and rollback mechanism testing
- Policy validation integration and compliance checking
- Cost estimation algorithms and calculation accuracy

### Integration Tests
- **Live Azure deployment** - no mocking of Azure Resource Manager APIs
- Complete infrastructure deployment lifecycle with real Azure resources
- Complex template dependency resolution and deployment ordering
- Policy enforcement with actual Azure Policy integration
- Large-scale resource group deployment performance testing
- Concurrent deployment scenarios with resource conflicts

### End-to-End Acceptance Tests
- Full simulation infrastructure deployment from Bicep/ARM specifications
- Integration with cost monitoring and governance enforcement systems
- Complex multi-tier application deployment with interdependent resources
- Deployment rollback and cleanup verification in failure scenarios
- Cross-component integration with orchestration and validation workflows

## Acceptance Criteria

- **Deployment Success Rate**: 99.5% success rate for syntactically valid templates
- **Performance**: Deploy standard infrastructure templates in under 8 minutes
- **Template Support**: Support for all Azure resource types and latest ARM features
- **Policy Compliance**: 100% integration with Azure Policy validation and enforcement
- **Cost Accuracy**: Cost estimates within 3% of actual Azure Resource Manager projections
- **Rollback Reliability**: Complete resource cleanup within 5 minutes for failed deployments
- **Concurrency**: Support 15+ concurrent resource group deployments
- **Error Diagnostics**: Detailed error reporting with actionable remediation guidance
- **Auditability**: Complete audit trail of all deployment operations and resource changes

## Open Questions

- Should we implement automatic Bicep module management and dependency resolution?
- What caching strategies can optimize repeated template deployment and compilation?
- How should we handle Azure resource provider registration and feature flag management?
- Should we implement custom ARM template functions for SimBuilder-specific operations?
- What approach should we use for handling Azure service regional availability and limitations?
- How do we optimize deployment performance for templates with hundreds of resources?
- Should we implement intelligent resource deployment ordering based on dependency analysis?
- What disaster recovery procedures should we implement for partially failed deployments?