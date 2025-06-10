# InfraSynthesis Agent Specification

## Purpose / Overview

Transforms resource plans into Infrastructure-as-Code (IaC) templates including Bicep, Terraform,
and ARM templates with proper dependency management and deployment strategies.

## Functional Requirements / User Stories

- Generate deployable IaC templates from resource plans
- Validate template syntax and dependency correctness
- Support multiple IaC providers (Terraform, Bicep, ARM)
- Optimize templates for cost and performance

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- Planner Agent (resource plans)
- Spec Library (template storage)
- Azure Resource Manager APIs
- Terraform/Bicep providers
- **Liquid Template Engine**: Runtime loading of prompts from `prompts/infrasynthesis/*.liquid`
  files
- **Prompt Templates**: External Liquid templates for Terraform generation, Bicep generation, and
  ARM template creation (no hard-coded prompts allowed)

## Documentation to Produce

- **IaC Template Generation Guide**: How the agent transforms resource plans into deployable
  templates
- **Multi-Provider Strategy**: Supporting Terraform, Bicep, and ARM template generation
- **Liquid Template Documentation**: Template variable definitions and usage patterns for
  `prompts/infrasynthesis/*.liquid` files
- **Prompt Template Guidelines**: Standards for creating, testing, and maintaining external Liquid
  prompt templates
- **Template Variable Schema**: Complete specification of all variables used across infrasynthesis
  prompt templates

## Testing Strategy

### Unit Tests

- IaC template syntax validation and correctness
- Resource dependency mapping and ordering
- Multi-provider template generation logic
- Liquid template loading and variable validation
- Template rendering with various resource plan scenarios
- Prompt template syntax validation and error handling

### Integration Tests

- **Live Azure services required** - no mocking of Azure Resource Manager APIs
- End-to-end template generation from resource plans to deployable artifacts
- Multi-provider template validation (Terraform, Bicep, ARM)
- External Liquid template loading from `prompts/infrasynthesis/` directory
- Template variable injection and rendering accuracy

### Acceptance Tests

- Complete IaC template generation for representative attack scenarios
- Template deployment success validation across multiple environments
- Prompt template lint validation in CI/CD pipeline
- Template variable completeness and consistency across all infrasynthesis prompts

## Acceptance Criteria

- Generate syntactically valid IaC templates
- Support complex multi-resource dependencies
- Achieve 95%+ deployment success rate
- Complete template generation within 60 seconds
- **Template Compliance**: All prompts MUST be loaded from external Liquid templates in
  `prompts/infrasynthesis/` directory
- **Template Quality**: All Liquid templates MUST pass CI/CD linting with valid syntax and complete
  variable definitions
- **Runtime Loading**: Template loading failures MUST cause graceful agent initialization failure
  with clear error messages

## Open Questions

- Multi-cloud template generation strategy?
- Template validation and testing pipeline?
- Custom resource provider integration?
