# Validator Agent Specification

## Purpose / Overview

The Validator Agent ensures that deployed simulation environments match their specifications and are
ready for attack execution. It validates infrastructure deployment state, verifies telemetry
collection configuration, confirms attack preconditions are met, and generates comprehensive
readiness assessments. This agent serves as the final quality gate before simulation environments
are handed off for testing.

## Functional Requirements / User Stories

- As a **Simulation Manager**, I need to verify that deployed environments exactly match the planned
  specifications before running attacks
- As a **Security Researcher**, I need confirmation that all telemetry collection points are
  properly configured to capture attack evidence
- As a **Red Team Member**, I need validation that attack preconditions (identities, permissions,
  data) are properly established
- As a **Operations Team**, I need automated validation reports that identify any deployment
  discrepancies or readiness issues
- As a **Compliance Officer**, I need verification that deployed environments meet security and
  governance requirements
- As a **Cost Manager**, I need validation that deployed resources align with approved budget and
  resource specifications
- As a **Quality Assurance**, I need comprehensive testing of environment connectivity and service
  availability

## Interfaces / APIs

### Inputs

- **DeploymentManifest objects**: Infrastructure deployment specifications and expected state
- **TelemetrySchema objects**: Expected monitoring and logging configurations
- **AttackSpec objects**: Attack scenario requirements and preconditions
- **Environment credentials**: Access credentials for validation testing
- **Validation rules**: Configurable validation criteria and thresholds

### Outputs

- **ValidationReport objects**: Comprehensive validation results with pass/fail status
- **ReadinessAssessment objects**: Environment readiness score and recommendations
- **Issue lists**: Detailed descriptions of validation failures and remediation steps
- **Telemetry verification**: Confirmation of monitoring setup and data flow
- **Performance metrics**: Environment response times and availability status

### Public Endpoints / CLI Commands

```
POST /validate/environment - Start environment validation
GET /validate/status/{validation_id} - Check validation progress
GET /validate/report/{validation_id} - Retrieve validation report
POST /validate/telemetry - Verify telemetry configuration
POST /validate/preconditions - Check attack preconditions
GET /validate/health - Agent health and capability status
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: For intelligent validation analysis and reporting
- **DataSeeder Agent**: Requires completion of data population before validation
- **Sentinel Analytics Integration**: For telemetry verification and log analysis
- **Graph Database Service**: For storing validation results and environment state
- **Core API Service**: For authentication and orchestration coordination
- **Azure Resource Manager**: For infrastructure state verification
- **Microsoft Graph/Entra Integration**: For identity and permission validation
- **Terraform/ARM Runners**: For deployment state confirmation
- **Liquid Template Engine**: Runtime loading of prompts from `prompts/validator/*.liquid` files
- **Prompt Templates**: External Liquid templates for environment validation, prerequisite checks,
  and telemetry verification (no hard-coded prompts allowed)

## Data Contracts / Schemas

### ValidationReport Schema

```yaml
ValidationReport:
  validation_id: string
  simulation_id: string
  timestamp: datetime
  status: enum [PASSED, FAILED, WARNING, IN_PROGRESS]
  overall_score: integer (0-100)
  categories:
    infrastructure: ValidationCategory
    telemetry: ValidationCategory
    security: ValidationCategory
    preconditions: ValidationCategory
  issues: array[ValidationIssue]
  recommendations: array[string]

ValidationCategory:
  status: enum [PASSED, FAILED, WARNING]
  score: integer (0-100)
  checks_performed: integer
  checks_passed: integer
  details: array[CheckResult]

ValidationIssue:
  severity: enum [CRITICAL, HIGH, MEDIUM, LOW]
  category: string
  description: string
  resource_id: string
  remediation_steps: array[string]
```

### Environment State Schema

```yaml
EnvironmentState:
  infrastructure:
    deployed_resources: array[ResourceStatus]
    network_connectivity: ConnectivityMatrix
    service_availability: array[ServiceStatus]
  identities:
    test_accounts: array[IdentityStatus]
    permissions: array[PermissionStatus]
    authentication_flows: array[AuthStatus]
  telemetry:
    log_collection: array[LogSourceStatus]
    monitoring_agents: array[AgentStatus]
    data_flow_verification: array[DataFlowStatus]
```

## Documentation to Produce

- **Validation Framework Guide**: Architecture and validation methodology
- **Custom Validation Rules**: How to configure validation criteria
- **Troubleshooting Playbook**: Common validation failures and resolutions
- **Telemetry Verification Guide**: Monitoring setup validation procedures
- **Integration Testing Guide**: End-to-end validation testing approaches
- **Performance Benchmarks**: Expected validation times and resource usage
- **Liquid Template Documentation**: Template variable definitions and usage patterns for
  `prompts/validator/*.liquid` files
- **Prompt Template Guidelines**: Standards for creating, testing, and maintaining external Liquid
  prompt templates
- **Template Variable Schema**: Complete specification of all variables used across validator prompt
  templates

## Testing Strategy

### Unit Tests

- Individual validation check implementations and logic
- Mock environment state validation scenarios
- Validation report generation and formatting
- Error handling for failed validation checks
- Configuration parsing and validation rule processing
- Integration with external service APIs
- Liquid template loading and variable validation
- Template rendering with various validation scenarios
- Prompt template syntax validation and error handling

### Integration Tests

- **Live Azure environment validation** - no mocking of Azure services
- Complete validation workflow with real deployed infrastructure
- Telemetry verification with actual Azure Monitor and Sentinel
- Identity validation with real Entra ID and Microsoft Graph
- Performance testing with large-scale simulation environments
- Error scenario testing with intentionally misconfigured environments
- External Liquid template loading from `prompts/validator/` directory
- Template variable injection and rendering accuracy

### End-to-End Acceptance Tests

- Full simulation lifecycle validation including deployment and validation
- Complex multi-tenant validation scenarios
- Attack precondition validation for sophisticated attack patterns
- Validation report accuracy and completeness verification
- Integration with GUI visualization of validation results
- Prompt template lint validation in CI/CD pipeline
- Template variable completeness and consistency across all validator prompts

## Acceptance Criteria

- **Validation Accuracy**: 99.5% accuracy in detecting configuration mismatches and readiness issues
- **Performance**: Complete validation of standard simulation in under 5 minutes
- **Coverage**: Validate 100% of critical infrastructure, security, and telemetry requirements
- **Reliability**: 99.9% agent uptime with automatic recovery from failures
- **Scalability**: Support concurrent validation of 10+ simulation environments
- **Reporting**: Generate comprehensive validation reports with actionable remediation steps
- **Integration**: Seamless integration with all deployment and monitoring components
- **Security**: Secure validation processes with minimal privilege escalation
- **Auditability**: Complete audit trail of all validation activities and results
- **Template Compliance**: All prompts MUST be loaded from external Liquid templates in
  `prompts/validator/` directory
- **Template Quality**: All Liquid templates MUST pass CI/CD linting with valid syntax and complete
  variable definitions
- **Runtime Loading**: Template loading failures MUST cause graceful agent initialization failure
  with clear error messages

## Open Questions

- What is the optimal balance between validation thoroughness and execution time?
- Should we implement progressive validation stages or comprehensive single-pass validation?
- How should we handle validation of ephemeral resources and dynamic configurations?
- What machine learning approaches could improve validation accuracy over time?
- Should we implement predictive validation to identify potential future issues?
- How do we handle validation of third-party integrations and external dependencies?
- What rollback mechanisms should trigger automatically based on validation failures?
- Should we implement collaborative validation with human review for complex scenarios?
