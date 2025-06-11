# CLI Interface Specification

## Session Management Commands

The CLI Interface provides comprehensive session management capabilities to support multiple
concurrent SimBuilder instances with isolated resources and dynamic port allocation.

### Session Management Commands

```bash
# Create new session with automatic port allocation
sim session create [--ports=custom-range]

# List all active sessions
sim session list

# Show detailed session information
sim session status [--session-id=UUID]

# Cleanup session resources
sim session cleanup [--session-id=UUID] [--force]

# Switch to different session context
sim session switch --session-id=UUID

# Export session environment variables
sim session env [--session-id=UUID] [--format=bash|powershell|json]
```

### Session-Aware Command Execution

All CLI commands automatically detect and use the current session context through:

- **Environment Variables**: `SIMBUILDER_SESSION_ID` and related session variables
- **Session File**: `.env.session` containing session-specific configuration
- **Port Discovery**: Automatic detection of allocated ports for service connections
- **Container Management**: Session-specific container operations and health checks

### Multi-Instance Support Features

- **Port Conflict Prevention**: Automatic port allocation and conflict resolution
- **Resource Isolation**: Session-specific containers, networks, and volumes
- **Concurrent Operations**: Support for multiple simultaneous SimBuilder instances
- **Session Cleanup**: Comprehensive cleanup of all session resources
- **GitHub Codespaces Integration**: Seamless operation in containerized development environments

## Purpose / Overview

The CLI Interface provides a rich command-line experience for SimBuilder, enabling developers,
security researchers, and operations teams to manage simulation environments through an intuitive
terminal interface. Built with Python's Rich library, it offers interactive workflows, real-time
progress visualization, and comprehensive simulation management capabilities while maintaining the
power and scriptability expected from enterprise CLI tools.

## Functional Requirements / User Stories

- As a **Developer**, I need a simple `simbuilder create` command to quickly spin up attack
  simulations
- As a **Security Researcher**, I need interactive prompts that guide me through attack scenario
  definition
- As a **Operations Engineer**, I need bulk operations and scripting capabilities for managing
  multiple simulations
- As a **System Administrator**, I need monitoring commands to track system health and resource
  usage
- As a **CI/CD Pipeline**, I need non-interactive modes for automated simulation testing
- As a **Team Lead**, I need reporting commands that generate summaries and cost breakdowns

## Interfaces / APIs

### Inputs

- **Command Line Arguments**: Simulation parameters, configuration files, and operation flags
- **Interactive Prompts**: User responses to clarification questions and configuration choices
- **Configuration Files**: YAML/JSON files with simulation specifications and preferences
- **Environment Variables**: Authentication credentials and default configuration settings
- **Stdin Pipes**: Batch operations and scripted automation inputs

### Outputs

- **Rich Console Output**: Formatted tables, progress bars, and status indicators
- **JSON/YAML Export**: Machine-readable output for automation and integration
- **Log Files**: Detailed operation logs for debugging and audit trails
- **Graph Visualizations**: ASCII art or terminal-based graph representations
- **Exit Codes**: Standard exit codes for scripting and automation integration

### Public REST / gRPC / CLI commands

````bash
# Simulation Management
simbuilder create [scenario-file] [--interactive] [--budget AMOUNT] [--ttl HOURS]
simbuilder list [--status STATUS] [--format json|table] [--all]
simbuilder show <simulation-id> [--graph] [--costs] [--resources]
simbuilder delete <simulation-id> [--force] [--cleanup-timeout SECONDS]

# Workflow Operations
simbuilder deploy <simulation-id> [--wait] [--timeout MINUTES]
simbuilder stop <simulation-id> [--immediate]
simbuilder logs <simulation-id> [--follow] [--agent AGENT_TYPE]

# Template Management
simbuilder templates list [--category CATEGORY] [--format json|table]
simbuilder templates show <template-name>
simbuilder templates create <template-file> [--validate]

# System Operations
simbuilder status [--detailed] [--format json|table]
simbuilder health [--services] [--agents]
simbuilder config [--set KEY=VALUE] [--get KEY] [--list]

# Reporting and Analytics
simbuilder report costs [--period DAYS] [--format json|csv]
simbuilder report usage [--by-user] [--by-simulation]
simbuilder export <simulation-id> [--format yaml|json] [--include-secrets]
### Core CLI Interface
```python
class SimBuilderCLI:
    """Main CLI application class with command groups and context management."""

    def __init__(self, config: CLIConfig):
        """Initialize CLI with configuration and API client."""

    def create_simulation(self, scenario_file: str = None, interactive: bool = False, **kwargs) -> str:
        """Create new simulation via Core API Service."""

    def list_simulations(self, status: str = None, format: str = "table") -> None:
        """List simulations with formatting options."""

    def show_simulation(self, simulation_id: str, graph: bool = False, costs: bool = False) -> None:
        """Display detailed simulation information."""

    def deploy_simulation(self, simulation_id: str, wait: bool = False) -> bool:
        """Start simulation deployment and optionally wait for completion."""

    def configure_system(self, key: str = None, value: str = None) -> None:
        """Manage system configuration via Configuration Service."""
````

### API Client Interface

```python
class APIClient:
    """HTTP client for Core API Service communication."""

    def authenticate(self) -> bool:
        """Authenticate with Core API Service using configured method."""

    def create_simulation(self, request: SimulationRequest) -> SimulationResponse:
        """Create simulation via POST /api/v1/simulations."""

    def get_simulations(self, filters: Dict[str, Any]) -> List[SimulationResponse]:
        """List simulations via GET /api/v1/simulations."""

    def get_simulation_status(self, simulation_id: str) -> SimulationStatus:
        """Get simulation status via GET /api/v1/simulations/{id}/status."""

    def stream_logs(self, simulation_id: str) -> Iterator[LogEntry]:
        """Stream simulation logs via WebSocket connection."""
```

### Consumer Components

The CLI Interface provides command-line access to:

- **Core API Service**: All simulation operations via
  [`APIClient.create_simulation()`](api_client.py:23) and management endpoints
- **Configuration Service**: System configuration via [`simbuilder config`](cli_commands.py:156) and
  [`ConfigurationPrompt.prompt_missing_config()`](config_prompt.py:12)
- **LLM Foundry Integration**: Interactive assistance via
  [`simbuilder create --interactive`](cli_commands.py:45) and chat completions
- **Spec Library**: Template management via [`simbuilder templates`](cli_commands.py:89) and
  specification operations
- **Tenant Discovery Agent**: Discovery operations via [`simbuilder discover`](cli_commands.py:123)
  command group
- **Graph Database Service**: Visualization via [`simbuilder show --graph`](cli_commands.py:67) and
  graph queries

````

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: For intelligent interactive guidance and assistance
- **Core API Service**: Primary backend for all CLI operations
- **Rich Python Library**: Terminal formatting, progress bars, and interactive elements
- **Click Framework**: Command-line argument parsing and subcommand structure
- **PyYAML**: Configuration file parsing and YAML output generation
- **Requests**: HTTP client for API communication
- **JWT Libraries**: Authentication token management
- **Colorama**: Cross-platform colored terminal output
- **External Prompt Templates**: All AI agent prompts are externalized to Liquid template files under `prompts/` directory

## Data Contracts / Schemas

### CLI Configuration
```python
class CLIConfig(BaseModel):
    api_endpoint: str = "https://api.simbuilder.local"
    default_region: str = "eastus"
    default_budget: float = 100.0
    default_ttl_hours: int = 24
    output_format: str = "table"
    auto_confirm: bool = False
    log_level: str = "INFO"
    auth_method: str = "device_code"

class CommandContext(BaseModel):
    config: CLIConfig
    api_client: APIClient
    user_id: str
    current_simulation: Optional[str]
    verbose: bool = False
    non_interactive: bool = False
````

### Interactive Workflow Data

```python
class InteractiveSession(BaseModel):
    session_id: str
    current_step: str
    collected_data: Dict[str, Any]
    remaining_questions: List[str]
    progress_percentage: float


class ProgressTracker(BaseModel):
    operation: str
    total_steps: int
    completed_steps: int
    current_step_name: str
    estimated_completion: Optional[datetime]
    errors: List[str]
```

## Documentation to Produce

- **CLI Reference Manual**: Complete command documentation with examples and use cases
- **Interactive Tutorial**: Step-by-step guide for new users
- **Scripting Guide**: Automation examples and best practices for CI/CD integration
- **Configuration Reference**: Environment variables, config files, and customization options
- **Troubleshooting Guide**: Common issues, error messages, and resolution steps
- **Integration Examples**: Using CLI with other tools and workflows

## Testing Strategy

### Unit Tests

- Command parsing and validation logic
- API client integration and error handling
- Configuration file loading and validation
- Output formatting and table generation
- Interactive prompt handling and state management
- Authentication token management and refresh

### Integration Tests

- **Live Core API Service required** - no mocking of backend API calls
- End-to-end simulation workflows from CLI commands
- Interactive session handling with real user input simulation
- File I/O operations for configuration and export functionality
- Authentication flows with real Azure AD integration
- Progress tracking and real-time updates during long operations

### Acceptance Tests

- Complete simulation lifecycle through CLI commands
- Bulk operations and scripting scenarios
- Cross-platform compatibility (Windows, macOS, Linux)
- Performance testing with large simulation lists and complex outputs
- Error handling and recovery scenarios
- Accessibility testing for screen readers and terminal limitations

## Acceptance Criteria

- **Usability**: Intuitive commands that follow CLI best practices and conventions
- **Performance**: Commands respond within 2 seconds for local operations, 10 seconds for API calls
- **Reliability**: Graceful error handling with helpful error messages and recovery suggestions
- **Automation**: Full scriptability with proper exit codes and machine-readable output
- **Accessibility**: Compatible with screen readers and keyboard-only navigation
- **Documentation**: Comprehensive help system accessible via `--help` flags
- **Cross-platform**: Consistent behavior across Windows, macOS, and Linux environments

## Open Questions

- Should we implement shell completion (bash, zsh, PowerShell) for better user experience?
- What level of offline functionality should we support when API is unavailable?
- How should we handle long-running operations - polling, WebSocket, or callback mechanisms?
- Should we implement configuration profiles for different environments (dev, staging, prod)?
- What approach should we use for secure credential storage across different platforms?
- Should we provide plugin architecture for custom commands and integrations?
- How do we handle API versioning and backward compatibility in CLI commands?
- Should we implement interactive TUI (Terminal User Interface) components for complex operations?
