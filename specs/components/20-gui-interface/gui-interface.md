# GUI Interface Specification

## Purpose / Overview

The GUI Interface provides a modern web-based dashboard for SimBuilder, enabling visual simulation management, real-time monitoring, and interactive graph exploration. Built with React and TypeScript, it offers intuitive workflows for creating simulations, monitoring progress, visualizing infrastructure relationships, and managing costs through responsive, accessible web interfaces that complement the CLI and API experiences.

## Functional Requirements / User Stories

- As a **Security Manager**, I need visual dashboards to monitor multiple simulations and resource utilization
- As a **Security Researcher**, I need interactive graph visualization to understand attack paths and infrastructure relationships
- As a **Team Lead**, I need cost management interfaces to track spending and budget compliance
- As a **Operations Engineer**, I need real-time monitoring views to track simulation health and performance
- As a **New User**, I need guided workflows that walk me through simulation creation step-by-step
- As a **Compliance Officer**, I need audit trail views and reporting interfaces for governance

## Design Decisions

- **MVP targets single-user workflow**: No real-time multi-user collaboration. Future ADR may add team collaboration.

## Interfaces / APIs

### Inputs
- **User Authentication**: OAuth2 flows and session management
- **Form Data**: Simulation creation forms and configuration interfaces
- **File Uploads**: Attack scenario files and configuration templates
- **Real-time Events**: WebSocket connections for live updates
- **User Preferences**: Dashboard customization and display settings

### Outputs
- **Interactive Dashboards**: Real-time simulation status and system health
- **Graph Visualizations**: 3D force-directed graphs using force-graph-3d
- **Reports and Exports**: PDF reports, CSV exports, and data visualizations
- **Notifications**: Real-time alerts and status updates
- **Configuration Downloads**: Generated templates and deployment artifacts

### Public REST / gRPC / CLI commands
```typescript
// Core React Components
<SimulationDashboard />
<SimulationCreator />
<GraphVisualization />
<CostManagement />
<SystemHealth />
<AuditLogs />

// API Integration Services
SimulationService.create(spec: AttackSpec): Promise<Simulation>
SimulationService.list(filters: FilterOptions): Promise<Simulation[]>
GraphService.getVisualizationData(id: string): Promise<GraphData>
CostService.getCostBreakdown(id: string): Promise<CostData>
WebSocketService.connect(simulationId: string): WebSocket
```

## Dependencies

- **Configuration Service**: For centralized configuration management and environment settings
- **LLM Foundry Integration**: For chat interfaces and intelligent user assistance
- **Core API Service**: Primary backend for all GUI operations
- **React 18+**: Modern React with hooks and concurrent features
- **TypeScript**: Type safety and development experience
- **Force-Graph-3D**: Interactive graph visualization library
- **Material-UI**: Component library for consistent design
- **React Query**: Data fetching and caching management
- **React Router**: Single-page application routing
- **WebSocket Client**: Real-time update connections
- **External Prompt Templates**: All AI agent prompts are externalized to Liquid template files under `prompts/` directory

## Data Contracts / Schemas

### Component Props and State
```typescript
interface SimulationDashboardProps {
  userId: string;
  initialFilters?: FilterOptions;
  refreshInterval?: number;
}

interface GraphVisualizationProps {
  simulationId: string;
  layout: '2d' | '3d';
  nodeTypes: NodeType[];
  interactionMode: 'explore' | 'edit';
}

interface CostManagementProps {
  simulationId?: string;
  timeRange: TimeRange;
  budgetLimits: BudgetConfiguration;
}

interface SimulationState {
  simulations: Simulation[];
  selectedSimulation?: Simulation;
  loading: boolean;
  error?: string;
  filters: FilterOptions;
}
```

### API Response Models
```typescript
interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  metadata: GraphMetadata;
}

interface GraphNode {
  id: string;
  type: string;
  name: string;
  properties: Record<string, any>;
  position?: { x: number; y: number; z: number };
  color?: string;
  size?: number;
}

interface CostData {
  totalCost: number;
  breakdown: CostBreakdown[];
  projections: CostProjection[];
  alerts: CostAlert[];
}
```

## Documentation to Produce

- **User Interface Guide**: Complete walkthrough of all GUI features and workflows
- **Component Documentation**: Storybook documentation for all React components
- **API Integration Guide**: How GUI components interact with backend services
- **Accessibility Guide**: WCAG compliance and keyboard navigation features
- **Theming and Customization**: Branding and appearance customization options
- **Deployment Guide**: Build processes, hosting, and CDN configuration

## Testing Strategy

### Unit Tests
- React component rendering and prop handling
- State management and reducer logic
- API service integration and error handling
- Form validation and user input processing
- Graph visualization component behavior
- WebSocket connection management

### Integration Tests
- **Live Core API Service required** - no mocking of backend API calls
- End-to-end user workflows through GUI interfaces
- Real-time updates via WebSocket connections
- File upload and download functionality
- Authentication flows and session management
- Cross-browser compatibility testing

### Acceptance Tests
- Complete simulation lifecycle through GUI workflows
- Graph visualization performance with large datasets
- Responsive design across desktop, tablet, and mobile devices
- Accessibility compliance with screen readers and keyboard navigation
- Performance testing with multiple concurrent users
- User experience testing with actual security researchers

## Acceptance Criteria

- **Performance**: Page load times under 3 seconds, smooth 60fps graph animations
- **Accessibility**: WCAG 2.1 AA compliance with full keyboard navigation support
- **Responsiveness**: Functional interface across desktop, tablet, and mobile devices
- **Reliability**: Graceful error handling with user-friendly error messages
- **Real-time**: Sub-second updates for simulation status and progress changes
- **Usability**: Intuitive workflows that require minimal training for new users
- **Security**: Secure authentication with automatic session timeout and CSRF protection

## Open Questions

- Should we implement offline functionality using service workers and local storage?
- What level of customization should we provide for dashboard layouts and widgets?
- How should we handle large graph visualizations (1000+ nodes) for performance?
- What mobile-specific features should we prioritize for field research scenarios?
- How do we handle theme customization and branding for different organizations?
- Should we implement guided tours or onboarding flows for new users?
- What approach should we use for handling real-time notifications and alerts?