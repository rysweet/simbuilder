# LLM Foundry Integration Specification

## Purpose / Overview

The LLM Foundry Integration component provides a single abstraction layer over Azure AI Foundry and azure-ai-openai SDKs for all LLM usage across the SimBuilder platform. This unified service enables consistent access to both reasoning (text completion) and chat completion models while handling authentication, routing, and operational concerns transparently.

## Functional Requirements

### Core Capabilities
- **Unified Client Interface**: Provide a single LLMClient supporting both "reasoning" (text completion) and "chat completion" models
- **Multi-Authentication Support**: Support two authentication modes with auto-detection via Configuration Service:
  - API KEY authentication
  - Azure AD bearer token authentication
- **Simple Async API**: Expose clean async interfaces:
  - `generateText(prompt, options)` - Text completion
  - `generateChat(messages, options)` - Chat completion  
  - `generateTextStream(prompt, options)` - Streaming text completion
  - `generateChatStream(messages, options)` - Streaming chat completion
  - Usage logging and metrics collection
- **Automatic Model Routing**: Route requests to appropriate models (GPT-4o, GPT-4-Turbo, GPT-35, etc.) based on configurable policy
- **Operational Features**:
  - Retry logic with exponential back-off
  - Token count budgeting and enforcement
  - Cost tracking and reporting
  - Request/response validation

### User Stories
- As a developer, I want to call LLM services without worrying about authentication details
- As a system administrator, I want centralized control over model selection and routing
- As a product owner, I want visibility into LLM usage and costs
- As a DevOps engineer, I want reliable LLM services with proper error handling and observability

## Non-Functional Requirements

### Performance
- **Response Time**: <800ms p95 latency for standard completions
- **Throughput**: Support 100+ concurrent requests
- **Streaming**: <200ms time-to-first-token for streaming responses

### Security
- **Secret Management**: Secure handling of API keys and bearer tokens
- **Data Privacy**: No logging of sensitive prompt/response content
- **Access Control**: Integration with tenant-based authorization

### Observability
- **Metrics**: Request count, latency, error rates, token usage, costs
- **Logging**: Structured logging with correlation IDs
- **Health Checks**: Service availability and dependency status

### Testability
- **Test Harness**: Local mock service for development and testing
- **Integration Tests**: Automated tests against real Azure services
- **Load Testing**: Performance validation under load

## Architecture & Design

### Core Components
- **LLMClient (Singleton)**: Main service interface with dependency injection
- **Adapter Pattern**: Abstraction layer around Azure AI Foundry SDK
- **Middleware Chain**: Pluggable middleware for retry, logging, tokenization
- **Model Router**: Policy-based routing to appropriate models
- **Usage Tracker**: Cost and token usage monitoring

### Key Interfaces
```typescript
interface LLMClient {
  generateText(prompt: string, options?: GenerationOptions): Promise<TextResponse>
  generateChat(messages: ChatMessage[], options?: GenerationOptions): Promise<ChatResponse>
  generateTextStream(prompt: string, options?: GenerationOptions): AsyncIterable<TextChunk>
  generateChatStream(messages: ChatMessage[], options?: GenerationOptions): AsyncIterable<ChatChunk>
}

interface GenerationOptions {
  model?: string
  maxTokens?: number
  temperature?: number
  timeout?: number
  retryPolicy?: RetryPolicy
}
```

### Authentication Flow
1. Configuration Service provides auth method and credentials
2. LLMClient auto-detects authentication mode
3. Adapter configures Azure SDK client with appropriate auth
### Middleware Pipeline
1. **Request Validation** - Schema validation and parameter sanitization
2. **Authentication** - Token management and credential validation  
3. **Rate Limiting** - Request throttling and quota enforcement
4. **Retry Logic** - Exponential backoff for transient failures
5. **Usage Tracking** - Token counting and cost calculation
6. **Response Processing** - Format standardization and error handling

## Interfaces / API Signatures

### Core LLM Client Interface
```python
class LLMClient:
    """Unified interface for Azure AI Foundry and OpenAI models."""
    
    @classmethod
    def get_instance() -> 'LLMClient':
        """Get singleton instance with configured authentication."""
        
    async def generate_text(self, prompt: str, options: GenerationOptions = None) -> TextResponse:
        """Generate text completion using reasoning models."""
        
    async def generate_chat(self, messages: List[ChatMessage], options: GenerationOptions = None) -> ChatResponse:
        """Generate chat completion using chat models."""
        
    async def generate_text_stream(self, prompt: str, options: GenerationOptions = None) -> AsyncIterator[TextChunk]:
        """Stream text completion with real-time token delivery."""
        
    async def generate_chat_stream(self, messages: List[ChatMessage], options: GenerationOptions = None) -> AsyncIterator[ChatChunk]:
        """Stream chat completion with real-time message delivery."""
        
    def get_usage_stats(self, timeframe: str = "24h") -> UsageStatistics:
        """Retrieve token usage and cost statistics."""
        
    async def health_check() -> HealthStatus:
        """Check service connectivity and model availability."""
```

### Request/Response Data Contracts
```python
class GenerationOptions(BaseModel):
    model: Optional[str] = None  # Auto-selected if not specified
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    timeout_seconds: Optional[int] = 30
    retry_policy: Optional[RetryPolicy] = None

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    name: Optional[str] = None

class TextResponse(BaseModel):
    text: str
    model_used: str
    tokens_used: int
    finish_reason: str
    response_id: str
    created_at: datetime

class ChatResponse(BaseModel):
    message: ChatMessage
    model_used: str
    tokens_used: int
    finish_reason: str
    response_id: str
    created_at: datetime

class UsageStatistics(BaseModel):
    total_requests: int
    total_tokens: int
    estimated_cost: float
    average_latency_ms: float
    error_rate: float
    by_model: Dict[str, ModelUsage]
```

### Authentication Interface
```python
class LLMAuthenticator:
    """Handles multi-authentication for Azure services."""
    
    def configure_api_key_auth(self, endpoint: str, api_key: str) -> bool:
        """Configure API key authentication."""
        
    def configure_bearer_token_auth(self, endpoint: str, token: str) -> bool:
        """Configure Azure AD bearer token authentication."""
        
    async def refresh_token_if_needed() -> bool:
        """Automatically refresh authentication tokens."""
        
    def get_auth_headers() -> Dict[str, str]:
        """Get current authentication headers for requests."""
```

### Model Router Interface
```python
class ModelRouter:
    """Policy-based routing to appropriate models."""
    
    def select_reasoning_model(self, context: RequestContext) -> str:
        """Select best reasoning model based on request characteristics."""
        
    def select_chat_model(self, context: RequestContext) -> str:
        """Select best chat model based on conversation context."""
        
    def update_routing_policy(self, policy: RoutingPolicy) -> bool:
        """Update model selection policies."""
        
    def get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Get model-specific capabilities and limits."""
```

### REST API Endpoints
```http
POST /llm/generate/text
  - Generate text completion
  - Request: {"prompt": "string", "options": GenerationOptions}
  - Response: TextResponse
  - Consumer: Tenant Discovery Agent, Core API Service

POST /llm/generate/chat
  - Generate chat completion  
  - Request: {"messages": [ChatMessage], "options": GenerationOptions}
  - Response: ChatResponse
  - Consumer: Core API Service, CLI Interface

GET /llm/generate/text/stream
  - Stream text completion via Server-Sent Events
  - Query params: prompt, model, max_tokens, temperature
  - Response: Stream of TextChunk events
  - Consumer: GUI Interface, CLI Interface

GET /llm/generate/chat/stream
  - Stream chat completion via Server-Sent Events
  - Query params: messages (JSON), model, max_tokens, temperature
  - Response: Stream of ChatChunk events
  - Consumer: GUI Interface

GET /llm/usage/statistics
  - Get usage statistics and costs
  - Query params: timeframe (1h, 24h, 7d, 30d)
  - Response: UsageStatistics
  - Consumer: Core API Service, Operations Dashboard

GET /llm/health
  - Service health and model availability
  - Response: {"status": "healthy", "models": ["gpt-4o"], "latency_ms": 150}
  - Consumer: Core API Service, Monitoring Systems

POST /llm/models/test
  - Test model connectivity and performance
  - Request: {"model": "gpt-4o", "test_prompt": "string"}
  - Response: {"success": true, "latency_ms": 200, "tokens": 50}
  - Consumer: System Administration, DevOps
```

### Consumer Components
The LLM Foundry Integration provides interfaces consumed by:
- **Tenant Discovery Agent**: Narrative generation via [`LLMClient.generate_text()`](llm_client.py:15)
- **Core API Service**: General text processing via [`LLMClient.generate_chat()`](llm_client.py:23)
- **CLI Interface**: Interactive assistance via [`LLMClient.generate_chat_stream()`](llm_client.py:31)
- **GUI Interface**: Real-time responses via [`LLMClient.generate_text_stream()`](llm_client.py:27)
- **Operations Dashboard**: Usage monitoring via [`LLMClient.get_usage_stats()`](llm_client.py:35)
- **System Health Checks**: Service monitoring via [`LLMClient.health_check()`](llm_client.py:39)
4. Middleware handles token refresh and error recovery

## Dependencies

- **Configuration Service**: For endpoint URLs, API keys, bearer tokens, and model policies
- **Service Bus**: For async job queuing if needed for long-running operations

## Acceptance Criteria

### Authentication Tests
- [ ] Successfully authenticate using API KEY method
- [ ] Successfully authenticate using Azure AD bearer token method
- [ ] Auto-detect authentication method from configuration
- [ ] Handle authentication failures gracefully

### Model Operation Tests
- [ ] Generate text completion using reasoning models
- [ ] Generate chat completion using chat models
- [ ] Stream text completion responses
- [ ] Stream chat completion responses
- [ ] Route requests to correct models based on policy

### Failure Handling Tests
- [ ] Retry failed requests with exponential backoff
- [ ] Handle rate limiting and quota exceeded errors
- [ ] Validate and reject malformed requests
- [ ] Timeout long-running requests appropriately

### Metrics and Monitoring Tests
- [ ] Track token usage and costs accurately
- [ ] Log request/response metrics without sensitive data
- [ ] Report service health and dependency status
- [ ] Generate usage reports by tenant/user

### Performance Tests
- [ ] Meet p95 latency requirements under normal load
- [ ] Handle 100+ concurrent requests
- [ ] Achieve <200ms time-to-first-token for streaming

## Open Questions

### Model Management
- **Model Versioning Strategy**: How should we handle model version updates and migrations?
- **Fine-tuning Storage**: Where should custom fine-tuned models be stored and managed?
- **Model Performance Monitoring**: How do we track and compare model performance over time?

### Integration Concerns
- **Streaming UI Hooks**: What client-side hooks are needed for streaming responses in the GUI?
- **Async Job Processing**: Should long-running LLM tasks use Service Bus for queuing?
- **Caching Strategy**: Should we cache frequent requests to reduce costs?

### Operational Questions
- **Cost Allocation**: How should costs be attributed across tenants and users?
- **Rate Limiting**: What rate limiting policies should be enforced per tenant?
- **Failover Strategy**: How should we handle Azure service outages?

## Source Alignment Note

Internal date: 2025-06-05

## Environment Configuration

### .env.template additions:
```bash
# Azure AI Foundry / OpenAI
AZURE_OPENAI_AUTH_METHOD=API_KEY        # or BEARER
AZURE_OPENAI_BEARER_TOKEN=              # populated when using Bearer
AZURE_OPENAI_MODEL_CHAT=gpt-4o
AZURE_OPENAI_MODEL_REASONING=gpt-4o