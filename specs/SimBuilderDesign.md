# SimBuilder Design

## 1 Architecture Overview

SimBuilder employs a distributed multi-agent architecture that separates concerns of planning, generation, orchestration, seeding, and validation.  Users drive the system from a CLI, Simple GUI, or MCP service. Agents communicate asynchronously over an Azure Service Bus topic and persist state in a shared metadata store. The design emphasises stateless execution for horizontal scalability on Azure Kubernetes Service (AKS), but in its primary form can all be run locally on a developer desktop. 

### Design Elements

* API service implements all functionality, CLI, GUI, MCP all talk to the API
* MVP Emphasis on ease of use for the developer building and trying the system locally
* Autogen Core (@https://microsoft.github.io/autogen/stable/ ) for agents framework
* AI Agents leverage knowledge frm Microsoft Learn and other sources to be experts in Azure automation
* Azure OpenAI for LLM
* Neo4J for database
* FASTAPI api service
* Rich CLI client
* React + typescript GUI client
* MCP service in front of API
* forcegraph3d for visualization of the graph database
* knowledge graph of relevant MS Learn artcles/content on azure services that the AI agents use in order to model "expertise" in Azure. 

_Figure&nbsp;1: Complete SimBuilder Architecture_

```mermaid
graph TD
    %% User Interfaces
    CLI[CLI Interface]
    GUI[GUI Interface]
    API[API Interface]
    MCP[MCP Service]
    
    %% Core API Service
    CORE[Core API Service]
    
    %% AI Agents
    CLARIFIER[Clarifier Agent]
    PLANNER[Planner Agent]
    INFRA[InfraSynthesis Agent]
    ORCH[Orchestrator Agent]
    SEEDER[DataSeeder Agent]
    VALIDATOR[Validator Agent]
    
    %% Data & State Management
    GRAPHDB[(Graph Database<br/>Neo4j)]
    SPECLIB[Spec Library<br/>Git Repository]
    BUS[(Azure Service Bus)]
    
    %% Azure Infrastructure
    ARM[Azure Resource Manager]
    TERRAFORM[Terraform Backend]
    AKS[Azure Kubernetes Service]
    
    %% Supporting Services
    FINOPS[FinOps & Cost Alerts]
    CLEANUP[Auto-cleanup Scheduler]
    SENTINEL[Sentinel & Log Analytics]
    ENTRA[Microsoft Graph & Entra]
    M365[Microsoft 365 APIs]
    
    %% User Interface Connections
    CLI --> CORE
    GUI --> CORE
    API --> CORE
    MCP --> CORE
    
    %% Core API to Agents
    CORE --> CLARIFIER
    CORE --> PLANNER
    CORE --> INFRA
    CORE --> ORCH
    CORE --> SEEDER
    CORE --> VALIDATOR
    
    %% Agent Interactions
    CLARIFIER --> PLANNER
    PLANNER --> INFRA
    INFRA --> ORCH
    ORCH --> SEEDER
    SEEDER --> VALIDATOR
    
    %% Data & Communication
    ORCH --> BUS
    BUS --> CLARIFIER
    BUS --> PLANNER
    BUS --> INFRA
    BUS --> SEEDER
    BUS --> VALIDATOR
    
    CORE --> GRAPHDB
    CLARIFIER --> GRAPHDB
    PLANNER --> GRAPHDB
    INFRA --> GRAPHDB
    SEEDER --> GRAPHDB
    VALIDATOR --> GRAPHDB
    
    PLANNER --> SPECLIB
    INFRA --> SPECLIB
    
    %% Infrastructure Deployment
    ORCH --> ARM
    ORCH --> TERRAFORM
    ARM --> AKS
    TERRAFORM --> AKS
    
    %% Supporting Service Integrations
    ORCH --> FINOPS
    ORCH --> CLEANUP
    VALIDATOR --> SENTINEL
    SEEDER --> ENTRA
    SEEDER --> M365
    
    %% Styling
    classDef interface fill:#e1f5fe
    classDef agent fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef azure fill:#fff3e0
    classDef support fill:#fce4ec
    
    class CLI,GUI,API,MCP interface
    class CLARIFIER,PLANNER,INFRA,ORCH,SEEDER,VALIDATOR agent
    class GRAPHDB,SPECLIB,BUS storage
    class ARM,TERRAFORM,AKS azure
    class FINOPS,CLEANUP,SENTINEL,ENTRA,M365 support
```

## 2 Agent Responsibilities

| Agent | Responsibility |
|-------|---------------|
| **PlannerAgent** | Convert high-level attack spec into concrete `ResourcePlan`. |
| **InfraSynthesisAgent** | Transform plan into IaC `DeploymentManifest`. |
| **DataSeeder** | Generate synthetic identities, mail, files, and logs. |
| **Validator** | Ensure deployed state matches prerequisites & telemetry expectations. |
| **Orchestrator** | Coordinate workflow via message bus and persist state. |

_Figure&nbsp;2: Complete MVP Flow Sequence_

```mermaid
sequenceDiagram
    participant U as User (CLI/GUI/API)
    participant API as Core API Service
    participant C as Clarifier Agent
    participant P as Planner Agent
    participant I as InfraSynthesis Agent
    participant O as Orchestrator Agent
    participant S as DataSeeder Agent
    participant V as Validator Agent
    participant DB as Graph Database
    participant GIT as Spec Library
    participant BUS as Service Bus
    participant ARM as Azure ARM/Terraform
    participant FIN as FinOps Service
    participant SENT as Sentinel/Analytics
    participant ENT as Entra/M365
    
    %% Initial Request
    U->>API: Submit attack scenario
    API->>C: Initialize clarification
    C->>DB: Store initial context
    
    %% Clarification Phase
    C->>U: Ask clarifying questions
    U->>C: Provide details
    C->>P: Send AttackSpec
    C->>BUS: Publish clarification complete
    
    %% Planning Phase
    P->>DB: Query existing patterns
    P->>GIT: Fetch relevant specs
    P->>I: Send ResourcePlan
    P->>BUS: Publish planning complete
    
    %% Infrastructure Synthesis
    I->>GIT: Retrieve IaC templates
    I->>DB: Validate dependencies
    I->>O: Send DeploymentManifest
    I->>BUS: Publish synthesis complete
    
    %% Orchestration & Deployment
    O->>FIN: Pre-deployment cost check
    FIN-->>O: Cost approval/warning
    O->>ARM: Deploy infrastructure
    ARM-->>O: Deployment status
    O->>DB: Update deployment state
    O->>S: Trigger data seeding
    O->>BUS: Publish deployment complete
    
    %% Data Seeding
    S->>ENT: Create test identities
    S->>ENT: Generate M365 content
    S->>DB: Record seeded data
    S->>V: Environment ready
    S->>BUS: Publish seeding complete
    
    %% Validation & Handoff
    V->>SENT: Verify telemetry setup
    V->>DB: Validate environment state
    V->>API: Environment validated
    API->>U: Ready notification + docs
    
    %% Background Monitoring
    Note over FIN: Continuous cost monitoring
    Note over O: Auto-cleanup scheduling
    Note over SENT: Telemetry collection
```


_Figure&nbsp;3: Data Flow and Integration Architecture_

```mermaid
graph LR
    %% Data Transformation Flow
    ATTACK[Attack Scenario]
    SPEC[AttackSpec]
    PLAN[ResourcePlan]
    MANIFEST[DeploymentManifest]
    TELEMETRY[TelemetrySchema]
    
    %% External Integrations
    subgraph "Microsoft Ecosystem"
        GRAPH[Microsoft Graph API]
        ENTRA[Entra ID]
        M365[Microsoft 365]
        SENTINEL[Sentinel]
        ANALYTICS[Log Analytics]
    end
    
    subgraph "Infrastructure Backends"
        ARM[Azure Resource Manager]
        TERRAFORM[Terraform Cloud/Enterprise]
        AKS[Azure Kubernetes Service]
    end
    
    subgraph "Cost & Operations"
        FINOPS[FinOps Service]
        COST[Cost Management API]
        CLEANUP[Auto-cleanup Scheduler]
        SCALE[AKS Auto-scaling]
    end
    
    subgraph "Data Storage"
        GRAPHDB[(Graph Database)]
        SPECREPO[Spec Repository<br/>Git]
        LOGS[(Log Storage)]
    end
    
    %% Data Flow
    ATTACK --> SPEC
    SPEC --> PLAN
    PLAN --> MANIFEST
    MANIFEST --> TELEMETRY
    TELEMETRY --> GRAPHDB
    
    %% Integration Flows
    MANIFEST --> ARM
    MANIFEST --> TERRAFORM
    ARM --> AKS
    TERRAFORM --> AKS
    
    SPEC --> ENTRA
    PLAN --> GRAPH
    MANIFEST --> M365
    TELEMETRY --> SENTINEL
    TELEMETRY --> ANALYTICS
    
    PLAN --> FINOPS
    FINOPS --> COST
    MANIFEST --> CLEANUP
    AKS --> SCALE
    
    SPEC --> SPECREPO
    PLAN --> SPECREPO
    TELEMETRY --> LOGS
    
    %% Feedback Loops
    FINOPS -.-> PLAN
    CLEANUP -.-> MANIFEST
    SENTINEL -.-> TELEMETRY
    
    %% Styling
    classDef dataflow fill:#e3f2fd
    classDef microsoft fill:#fff3e0
    classDef infrastructure fill:#e8f5e8
    classDef operations fill:#fce4ec
    classDef storage fill:#f3e5f5
    
    class ATTACK,SPEC,PLAN,MANIFEST,TELEMETRY dataflow
    class GRAPH,ENTRA,M365,SENTINEL,ANALYTICS microsoft
    class ARM,TERRAFORM,AKS infrastructure
    class FINOPS,COST,CLEANUP,SCALE operations
    class GRAPHDB,SPECREPO,LOGS storage
```

## 4 Data Model

The system transforms user input through a series of structured data objects:

```text
AttackSpec → ResourcePlan → DeploymentManifests → TelemetrySchema → GraphDB representation
```

### Core Data Objects:
- **AttackSpec**: Structured representation of user's attack scenario requirements
- **ResourcePlan**: Concrete Azure resources and configurations needed
- **DeploymentManifest**: Infrastructure-as-Code templates and deployment scripts
- **TelemetrySchema**: Expected logs, metrics, and monitoring configurations
- **GraphDB Node**: Persistent representation linking all components and relationships

## 5 Integration Points

- Microsoft Graph & Entra ID for tenant and identity operations.  
- Azure Resource Manager or Terraform for infrastructure deployment.  
- Microsoft 365 APIs for workload data.  
- Sentinel & Log Analytics for telemetry collection.  

## 6 Testing & Governance

- **Unit & contract tests** executed per micro-service in isolated sandbox.  
- **Canary environments** validated nightly with representative attack library.  
- **Policy guardrails** (Azure Policy, Defender for Cloud) enforced pre-merge.  

