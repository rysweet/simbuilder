# DataSeeder Agent Specification

## Purpose / Overview
Generates synthetic identities, data relationships, and realistic content to populate simulation environments with believable organizational structures, user activities, and attack preconditions.

## Functional Requirements / User Stories
- Generate synthetic identities and organizational structures
- Create realistic data relationships across tenants and workloads
- Populate Microsoft 365 environments with synthetic content
- Establish attack preconditions and target relationships

## Dependencies
- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: For intelligent synthetic data generation and content creation
- Microsoft Graph/Entra Integration
- Microsoft 365 Integration
- Graph Database Service
- Orchestrator Agent
- **Liquid Template Engine**: Runtime loading of prompts from `prompts/dataseeder/*.liquid` files
- **Prompt Templates**: External Liquid templates for identity generation, data population, and relationship mapping (no hard-coded prompts allowed)

## Documentation to Produce
- **Synthetic Data Generation Guide**: How the agent creates realistic organizational structures and user data
- **Cross-Tenant Relationship Modeling**: Strategies for establishing believable data relationships
- **Liquid Template Documentation**: Template variable definitions and usage patterns for `prompts/dataseeder/*.liquid` files
- **Prompt Template Guidelines**: Standards for creating, testing, and maintaining external Liquid prompt templates
- **Template Variable Schema**: Complete specification of all variables used across dataseeder prompt templates

## Testing Strategy

### Unit Tests
- Synthetic identity generation logic and realism validation
- Data relationship mapping and cross-reference creation
- Microsoft 365 content population algorithms
- Liquid template loading and variable validation
- Template rendering with various data seeding scenarios
- Prompt template syntax validation and error handling

### Integration Tests
- **Live Microsoft Graph/365 services required** - no mocking of identity and content APIs
- End-to-end data seeding with real Microsoft 365 environments
- Cross-tenant relationship establishment and validation
- External Liquid template loading from `prompts/dataseeder/` directory
- Template variable injection and rendering accuracy

### Acceptance Tests
- Complete data seeding for representative attack scenarios
- Realistic organizational structure and user activity validation
- Prompt template lint validation in CI/CD pipeline
- Template variable completeness and consistency across all dataseeder prompts

## Acceptance Criteria
- Generate realistic organizational data structures
- Create believable user activities and relationships
- Support attack scenario precondition setup
- Complete data seeding within acceptable timeframes
- **Template Compliance**: All prompts MUST be loaded from external Liquid templates in `prompts/dataseeder/` directory
- **Template Quality**: All Liquid templates MUST pass CI/CD linting with valid syntax and complete variable definitions
- **Runtime Loading**: Template loading failures MUST cause graceful agent initialization failure with clear error messages

## Open Questions
- Synthetic data generation strategies and realism requirements?
- Data privacy and compliance considerations?
- Cross-tenant relationship modeling approaches?