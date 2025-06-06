# Configuration Service Specification

## Purpose / Overview
The Configuration Service provides centralized configuration management for all SimBuilder modules. It handles loading, validating, and distributing configuration parameters across the entire application ecosystem, ensuring consistent and secure access to environment-specific settings, API keys, and operational parameters.

## Primary Functional Requirements

### Configuration Loading & Management
- **Environment File Loading**: Load configuration from `.env` file at application startup with intelligent defaults for local development environments
- **Template Generation**: Provide comprehensive `.env.template` file containing all critical configuration parameters with example values and documentation
- **Fail-Fast on Missing Config**: When configuration file is missing, immediately fail startup, automatically copy `.env.template` to `.env`, and log clear instructional message for user action
- **Partial Configuration Handling**: Detect when critical configuration keys are missing (e.g., AZURE_OPENAI_KEY, database credentials) and prompt user interactively via CLI or GUI to complete configuration
- **Programmatic API**: Offer clean, type-safe API for other modules to read configuration values, with write capabilities restricted to development environments only
- **Hot-Reload Support**: Monitor configuration file changes during development and automatically reload configuration without requiring application restart

### Configuration Validation & Security
- **Input Validation**: Validate all configuration values against expected formats, ranges, and constraints
- **Secret Management**: Secure handling of sensitive configuration data with appropriate masking in logs and error messages
- **Environment Separation**: Clear separation between development, staging, and production configuration handling

## Non-Functional Requirements

### Security
- **Secret Protection**: Ensure sensitive configuration values are never logged or exposed in plain text
- **Access Control**: Implement role-based access to configuration modification capabilities
- **Encryption**: Support encrypted storage of sensitive configuration values in production environments

### Compliance & Standards
- **12-Factor App Compliance**: Full adherence to 12-factor app methodology for configuration management
- **Environment Variable Standards**: Follow standard naming conventions and hierarchical organization

### Performance & Reliability
- **Thread Safety**: Ensure all configuration access is thread-safe for concurrent module access
- **Low Latency**: Provide sub-millisecond configuration value retrieval for performance-critical paths
- **Fault Tolerance**: Graceful handling of configuration file corruption or temporary inaccessibility

### Testability
- **Mock Support**: Provide test-friendly configuration injection mechanisms
- **Isolation**: Support isolated configuration contexts for unit and integration testing

## Architecture & Design

### Core Components
- **ConfigManager (Singleton)**: Central configuration management class implementing singleton pattern for global access
- **DotEnv Parser**: Robust parsing of environment files with support for comments, multi-line values, and variable interpolation
- **Validation Layer**: Comprehensive validation engine with configurable rules and custom validators
- **Change Detection**: File system watcher for hot-reload functionality during development
- **Prompt Integration**: Seamless integration with CLI and GUI components for interactive configuration completion

### Integration Points
- **CLI Interface**: Command-line prompts for missing configuration completion
- **GUI Interface**: User-friendly forms for configuration management in GUI mode
- **Logging System**: Structured logging of configuration events and errors
- **Service Discovery**: Registration with service bus for configuration change notifications

## Dependencies

### Runtime Dependencies
- None (self-contained for maximum reliability)

### Development Dependencies
- **Python**: python-dotenv for environment file parsing, watchdog for file monitoring
- **Node.js**: dotenv package, chokidar for file watching
### Dependent Components (Consumers)
The Configuration Service is consumed by all SimBuilder components:
- **Core API Service**: Service endpoint configuration and authentication settings
- **Graph Database Service**: Database connection parameters and Neo4j configuration
- **Service Bus**: Message broker configuration and connection strings
- **Spec Library**: Git repository configuration and storage settings
- **LLM Foundry Integration**: Azure OpenAI credentials and model configuration
- **Tenant Discovery Agent**: Azure authentication and discovery scope settings
- **CLI Interface**: Default settings and interactive configuration prompts
- **All Other Components**: Environment-specific settings and operational parameters
- **File System**: Native file system APIs for configuration file operations

## Acceptance Criteria

### Core Functionality
- [ ] Application fails fast with clear error message when `.env` file is missing
- [ ] `.env.template` is automatically copied to `.env` on missing configuration
- [ ] Interactive prompts appear when critical configuration keys are missing
- [ ] All modules can successfully read configuration through provided API
- [ ] Configuration changes are hot-reloaded during development without restart
- [ ] Write operations are properly restricted in production environments

### Error Handling & User Experience
- [ ] Clear, actionable error messages for all configuration issues
- [ ] Graceful degradation when non-critical configuration is missing
- [ ] Comprehensive logging of configuration loading and validation events

### Testing & Quality
- [ ] 100% unit test coverage for all configuration management functions
- [ ] Integration tests validate interaction with dependent modules
- [ ] Performance tests confirm sub-millisecond configuration retrieval
- [ ] Security tests verify proper handling of sensitive data

### Documentation & Templates
- [ ] Complete `.env.template` with all required and optional parameters
- [ ] Clear documentation for configuration parameter purposes and formats
- [ ] Developer guide for adding new configuration parameters
## Interfaces / API Signatures

### Configuration Loading Interface
```python
class ConfigManager:
    """Singleton configuration manager providing centralized access to all configuration values."""
    
    @classmethod
    def get_instance() -> 'ConfigManager':
        """Get singleton instance of ConfigManager."""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve configuration value by key with optional default."""
        
    def get_required(self, key: str) -> Any:
        """Retrieve required configuration value, raise ConfigurationError if missing."""
        
    def get_section(self, section_prefix: str) -> Dict[str, Any]:
        """Get all configuration keys with specified prefix as dictionary."""
        
    def reload() -> bool:
        """Hot-reload configuration from file, return True if successful."""
        
    def validate() -> List[ValidationError]:
        """Validate all configuration values, return list of errors."""
        
    def is_development() -> bool:
        """Check if running in development environment."""
        
    def mask_sensitive(self, value: str, key: str) -> str:
        """Mask sensitive configuration values for logging."""
```

### Configuration Validation Interface
```python
class ConfigValidator:
    """Configuration validation engine with extensible rules."""
    
    def validate_azure_credentials() -> ValidationResult:
        """Validate Azure authentication configuration."""
        
    def validate_database_connection() -> ValidationResult:
        """Validate database connection parameters."""
        
    def validate_service_endpoints() -> ValidationResult:
        """Validate all service endpoint configurations."""
        
    def validate_security_settings() -> ValidationResult:
        """Validate security-related configuration parameters."""
```

### Interactive Configuration Interface
```python
class ConfigurationPrompt:
    """Interactive configuration completion for missing parameters."""
    
    def prompt_missing_config() -> Dict[str, str]:
        """Prompt user for missing critical configuration values."""
        
    def validate_user_input(key: str, value: str) -> bool:
        """Validate user-provided configuration value."""
        
    def save_configuration(config_updates: Dict[str, str]) -> bool:
        """Save updated configuration to .env file."""
```

### REST API Endpoints
```http
GET /config/health
  - Check configuration service health and validation status
  - Response: {"status": "healthy", "validation_errors": []}

GET /config/template
  - Retrieve current .env.template content
  - Response: Plain text .env.template file

POST /config/validate
  - Validate current configuration
  - Request: {"section": "optional_section_filter"}
  - Response: {"valid": true, "errors": [], "warnings": []}

GET /config/environment
  - Get current environment context (development/staging/production)
  - Response: {"environment": "development", "debug_mode": true}
```

### Consumer Components
The Configuration Service provides interfaces consumed by:
- **All SimBuilder Components**: Core configuration loading via [`ConfigManager.get()`](config_manager.py:15)
- **Core API Service**: Environment validation via [`ConfigValidator.validate_service_endpoints()`](config_validator.py:23)
- **Graph Database Service**: Database connection parameters via [`ConfigManager.get_section("GRAPH_DB")`](config_manager.py:31)
- **Service Bus**: Message broker configuration via [`ConfigManager.get_section("SERVICE_BUS")`](config_manager.py:31)
- **LLM Foundry Integration**: Azure OpenAI credentials via [`ConfigManager.get_section("AZURE_OPENAI")`](config_manager.py:31)
- **Tenant Discovery Agent**: Azure authentication via [`ConfigManager.get_section("AZURE")`](config_manager.py:31)
- **CLI Interface**: Interactive configuration prompts via [`ConfigurationPrompt.prompt_missing_config()`](config_prompt.py:12)

## Environment Template

```env
# =============================================================================
# SimBuilder Configuration Template
# =============================================================================
# Copy this file to .env and update values for your environment
# Remove this header section after copying

# --- Core Services ---
CORE_API_URL=http://localhost:7000
CORE_API_PORT=7000

# --- Graph Database Configuration ---
GRAPH_DB_URI=neo4j://localhost:7687
GRAPH_DB_USER=neo4j
GRAPH_DB_PASSWORD=changeme
GRAPH_DB_DATABASE=simbuilder

# --- Service Bus Configuration ---
SERVICE_BUS_URL=amqp://localhost:5672
SERVICE_BUS_USER=guest
SERVICE_BUS_PASSWORD=guest

# --- Azure OpenAI Configuration ---
AZURE_OPENAI_ENDPOINT=https://<your-endpoint>.openai.azure.com/
AZURE_OPENAI_KEY=changeme
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1

# --- Azure AI Foundry / OpenAI ---
AZURE_OPENAI_AUTH_METHOD=API_KEY        # or BEARER
AZURE_OPENAI_BEARER_TOKEN=              # populated when using Bearer
AZURE_OPENAI_MODEL_CHAT=gpt-4o
AZURE_OPENAI_MODEL_REASONING=gpt-4o

# --- Microsoft Graph & Entra Integration ---
AZURE_CLIENT_ID=changeme
AZURE_CLIENT_SECRET=changeme
GRAPH_API_SCOPE=https://graph.microsoft.com/.default

# --- Application Configuration ---
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG_MODE=true
MAX_CONCURRENT_SIMULATIONS=10

# --- Security Configuration ---
JWT_SECRET_KEY=changeme-generate-random-key
SESSION_TIMEOUT_MINUTES=60
ENCRYPTION_KEY=changeme-32-character-key

# --- External Integrations ---
SENTINEL_WORKSPACE_ID=changeme
TERRAFORM_STATE_STORAGE_ACCOUNT=changeme
BICEP_TEMPLATE_STORAGE=changeme
```

## Open Questions

### User Experience
- **Prompting Strategy**: Should configuration prompts be CLI-only, GUI-only, or adaptive based on execution context?
- **Validation Feedback**: How detailed should validation error messages be for non-technical users?
- **Configuration Wizards**: Should we provide guided setup wizards for complex configurations?

### Production Considerations
- **Secret Storage**: Integration with Azure Key Vault or other secret management systems for production deployments?
- **Configuration Hierarchy**: Support for environment-specific configuration overlays (dev/staging/prod)?
- **Cloud Configuration**: Integration with Azure App Configuration or similar cloud configuration services?

### Advanced Features
- **Configuration Versioning**: Should configuration changes be versioned and auditable?
- **Remote Configuration**: Support for pulling configuration from remote sources?
- **Configuration Validation API**: Expose configuration validation as a service for other components?

## Source Alignment Note
*This specification was created as an internal SimBuilder component specification on 2025-06-05 to address centralized configuration management requirements across all project modules.*