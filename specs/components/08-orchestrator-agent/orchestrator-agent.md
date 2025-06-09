# Orchestrator Agent Specification

## Purpose / Overview
Coordinates the entire simulation deployment workflow, manages resource provisioning, monitors deployment progress, and handles rollback scenarios. Serves as the central coordinator for all deployment activities.

## Functional Requirements / User Stories
- Orchestrate multi-step deployment workflows
- Coordinate with IaC providers (Terraform, ARM/Bicep)
- Monitor deployment progress and handle failures
- Manage resource cleanup and rollback procedures

## Dependencies
- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: For intelligent deployment orchestration and status updates
- InfraSynthesis Agent (deployment manifests)
- Terraform Runner and ARM/Bicep Runner
- Service Bus (workflow coordination)
- FinOps Alerting (cost monitoring)
- **Liquid Template Engine**: Runtime loading of prompts from `prompts/orchestrator/*.liquid` files
- **Prompt Templates**: External Liquid templates for deployment orchestration and status updates (no hard-coded prompts allowed)

## Documentation to Produce
- **Deployment Orchestration Guide**: How the agent coordinates complex multi-step deployments
- **Workflow Management Strategy**: Handling dependencies, failures, and rollback procedures
- **Liquid Template Documentation**: Template variable definitions and usage patterns for `prompts/orchestrator/*.liquid` files
- **Prompt Template Guidelines**: Standards for creating, testing, and maintaining external Liquid prompt templates
- **Template Variable Schema**: Complete specification of all variables used across orchestrator prompt templates

## Testing Strategy

### Unit Tests
- Deployment workflow logic and state management
- Error handling and rollback procedures
- Service integration and coordination logic
- Liquid template loading and variable validation
- Template rendering with various deployment scenarios
- Prompt template syntax validation and error handling

### Integration Tests
- **Live Azure services required** - no mocking of deployment services
- End-to-end deployment orchestration with real infrastructure
- Multi-provider coordination (Terraform, ARM/Bicep)
- External Liquid template loading from `prompts/orchestrator/` directory
- Template variable injection and rendering accuracy

### Acceptance Tests
- Complete deployment orchestration for representative attack scenarios
- Rollback and failure recovery validation
- Prompt template lint validation in CI/CD pipeline
- Template variable completeness and consistency across all orchestrator prompts

## Acceptance Criteria
- Successfully orchestrate complex multi-resource deployments
- Handle deployment failures with proper rollback
- Complete deployments within expected timeframes
- Provide real-time progress updates
- **Template Compliance**: All prompts MUST be loaded from external Liquid templates in `prompts/orchestrator/` directory
- **Template Quality**: All Liquid templates MUST pass CI/CD linting with valid syntax and complete variable definitions
- **Runtime Loading**: Template loading failures MUST cause graceful agent initialization failure with clear error messages

## Open Questions
- Deployment orchestration strategy for complex dependencies?
- Rollback procedures and state management?
- Integration with multiple IaC providers?