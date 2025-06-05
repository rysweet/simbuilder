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