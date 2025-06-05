# Clarifier Agent Specification

## Purpose / Overview

The Clarifier Agent transforms user-provided attack scenarios into structured, complete attack specifications through interactive questioning and requirements gathering. Using Microsoft's Autogen Core framework and Azure OpenAI, it systematically identifies missing details, clarifies ambiguous requirements, and ensures all necessary information is captured for downstream planning and synthesis. The agent serves as the intelligent front-end that bridges natural language attack descriptions to formal specifications.

## Functional Requirements / User Stories

- As a **Security Researcher**, I need to provide a brief attack description and have the system ask intelligent clarifying questions
- As a **Red Team Member**, I need the system to understand domain-specific terminology and attack patterns
- As a **User**, I need progressive disclosure of questions, starting with the most critical missing information
- As a **Planner Agent**, I need complete, structured attack specifications with all dependencies clearly defined
- As a **Core API Service**, I need real-time updates on clarification progress and completion status
- As a **System Administrator**, I need visibility into common clarification patterns for template improvement
- Ask only high-impact missing details; infer remaining fields with sensible defaults to minimize user prompt fatigue.

## Interfaces / APIs

### Inputs
- **Raw Attack Scenarios**: Natural language descriptions of attacks, environments, or requirements
- **User Responses**: Answers to clarifying questions via API callbacks
- **Domain Knowledge**: Microsoft Learn articles, MITRE ATT&CK framework, Azure service documentation
- **Template Library**: Pre-existing attack patterns and specifications for reference
- **Context Information**: User role, organization, and historical attack patterns

### Outputs
- **Clarifying Questions**: Intelligent, progressive questions to gather missing information
- **Attack Specifications**: Structured YAML/JSON specifications ready for planning
- **Confidence Scores**: Completeness assessment for each specification section
- **Recommendations**: Suggested attack variations and alternative approaches
- **Progress Updates**: Real-time status via Service Bus messaging

### Public REST / gRPC / CLI commands
```
POST /clarifier/sessions - Start new clarification session
POST /clarifier/sessions/{id}/responses - Submit answer to clarification question
GET /clarifier/sessions/{id}/status - Get current session progress
GET /clarifier/sessions/{id}/questions - Get current outstanding questions
POST /clarifier/sessions/{id}/complete - Finalize attack specification
GET /clarifier/sessions/{id}/specification - Retrieve completed specification
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: GPT-4 for natural language processing and question generation
- **Core API Service**: Session management and user authentication
- **Graph Database Service**: Storing partial specifications and relationship modeling
- **Service Bus**: Publishing clarification progress and completion events
- **Spec Library**: Access to template library and historical attack patterns
- **Microsoft Learn Knowledge Base**: Azure service expertise and best practices
- **Liquid Template Engine**: Runtime loading of prompts from `prompts/clarifier/*.liquid` files
- **Prompt Templates**: External Liquid templates for question generation, follow-up queries, and specification creation (no hard-coded prompts allowed)

## Data Contracts / Schemas

### Clarification Session Data
```python
class ClarificationSession(BaseModel):
    session_id: str
    user_id: str
    original_scenario: str
    current_specification: PartialAttackSpec
    outstanding_questions: List[ClarifyingQuestion]
    answered_questions: List[AnsweredQuestion]
    confidence_score: float
    completion_status: SessionStatus

class ClarifyingQuestion(BaseModel):
    question_id: str
    text: str
    category: QuestionCategory
    priority: int
    suggested_answers: List[str]
    requires_domain_knowledge: bool
    depends_on: List[str]  # Other question IDs

class QuestionCategory(str, Enum):
    TARGET_ENVIRONMENT = "target_environment"
    ATTACK_VECTORS = "attack_vectors"
    SCOPE_AND_SCALE = "scope_and_scale"
    TELEMETRY_REQUIREMENTS = "telemetry_requirements"
    BUDGET_AND_TIMING = "budget_and_timing"
    COMPLIANCE_CONSTRAINTS = "compliance_constraints"

class PartialAttackSpec(BaseModel):
    scenario_name: Optional[str]
    attack_description: str
    target_environment: Optional[TargetEnvironment]
    attack_vectors: List[AttackVector]
    required_identities: List[IdentityRequirement]
    expected_telemetry: List[TelemetryRequirement]
    budget_constraints: Optional[BudgetConstraint]
    timeline_requirements: Optional[TimelineRequirement]
    completeness_scores: Dict[str, float]
```

### AI Agent Configuration
```python
class ClarifierConfig(BaseModel):
    model_name: str = "gpt-4"
    temperature: float = 0.3
    max_questions_per_session: int = 20
    confidence_threshold: float = 0.85
    domain_knowledge_sources: List[str]
    question_generation_prompts: Dict[str, str]
```

## Documentation to Produce

- **Question Generation Strategies**: How the agent constructs intelligent clarifying questions
- **Domain Knowledge Integration**: Leveraging Microsoft Learn and MITRE ATT&CK data
- **Natural Language Processing**: Text analysis and intent recognition techniques
- **Session Management Guide**: Handling partial sessions, timeouts, and recovery
- **Liquid Template Documentation**: Template variable definitions and usage patterns for `prompts/clarifier/*.liquid` files
- **Prompt Template Guidelines**: Standards for creating, testing, and maintaining external Liquid prompt templates
- **Template Variable Schema**: Complete specification of all variables used across clarifier prompt templates
- **Knowledge Base Curation**: Maintaining and updating domain expertise sources

## Testing Strategy

### Unit Tests
- Natural language parsing and intent extraction
- Question generation logic and prioritization
- Specification completeness assessment
- Domain knowledge integration and lookup
- Session state management and persistence
- Liquid template loading and variable validation
- Template rendering with various input scenarios
- Prompt template syntax validation and error handling

### Integration Tests
- **Live Azure OpenAI required** - no mocking of AI services
- End-to-end clarification sessions with real user interactions
- Multi-turn conversation handling and context maintenance
- Integration with Graph Database for specification storage
- Service Bus messaging for workflow coordination
- Knowledge base queries and domain expertise retrieval
- External Liquid template loading from `prompts/clarifier/` directory
- Template variable injection and rendering accuracy

### Acceptance Tests
- Complete attack scenario clarification from vague descriptions
- Domain expert validation of generated questions and specifications
- Multi-user concurrent clarification sessions
- Knowledge base accuracy and relevance testing
- Performance benchmarks for question generation and response times
- Prompt template lint validation in CI/CD pipeline
- Template variable completeness and consistency across all clarifier prompts

## Acceptance Criteria

- **Intelligence**: Generate relevant, non-redundant questions that efficiently gather missing information
- **Efficiency**: Complete clarification in 5-15 questions for typical attack scenarios
- **Accuracy**: Achieve 90%+ completeness scores for critical specification sections
- **Usability**: Provide clear, jargon-free questions with helpful suggested answers
- **Performance**: Generate questions within 3 seconds and process responses within 2 seconds
- **Knowledge**: Demonstrate expertise in Azure services, security concepts, and attack patterns
- **Reliability**: Handle session interruptions and resume clarification effectively
- **Template Compliance**: All prompts MUST be loaded from external Liquid templates in `prompts/clarifier/` directory
- **Template Quality**: All Liquid templates MUST pass CI/CD linting with valid syntax and complete variable definitions
- **Runtime Loading**: Template loading failures MUST cause graceful agent initialization failure with clear error messages

## Open Questions

- What domain knowledge sources should we prioritize for continuous learning and updates?
- Should we implement adaptive questioning based on user expertise level and role?
- How do we handle conflicting or contradictory answers within a clarification session?
- What mechanisms should we use for continuous improvement of question quality?
- Should we implement collaborative clarification sessions for team-based attack planning?
- How do we ensure generated questions remain current with evolving Azure services and attack patterns?
- What privacy and security considerations apply to storing partial attack specifications?