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

```text
LLM ↔ Knowledge Base ↔ Constraint Solver → IaC Emitter
```

_Figure&nbsp;1: High-level agent interaction_

```mermaid
graph TD
  User-->Clarifier
  Clarifier-->Planner
  Planner-->InfraSynthesis
  InfraSynthesis-->Orchestrator
  Orchestrator-->Azure[Azure Resource Manager]
  Orchestrator-->DataSeeder
  DataSeeder-->Validator
  Validator-->User
  Orchestrator-->Bus[(Service Bus)]
  subgraph Agents
    Clarifier
    Planner
    InfraSynthesis
    DataSeeder
    Validator
  end
```

## 2 Agent Responsibilities

| Agent | Responsibility |
|-------|---------------|
| **PlannerAgent** | Convert high-level attack spec into concrete `ResourcePlan`. |
| **InfraSynthesisAgent** | Transform plan into IaC `DeploymentManifest`. |
| **DataSeeder** | Generate synthetic identities, mail, files, and logs. |
| **Validator** | Ensure deployed state matches prerequisites & telemetry expectations. |
| **Orchestrator** | Coordinate workflow via message bus and persist state. |

_Figure&nbsp;2: Deployment sequence flow_

```mermaid
sequenceDiagram
  participant U as User
  participant C as Clarifier
  participant P as Planner
  participant I as InfraSynth
  participant O as Orchestrator
  participant A as Azure
  participant S as DataSeeder
  participant V as Validator
  U->>C: Describe attack
  C->>U: Clarifying Qs
  C->>P: AttackSpec
  P->>I: ResourcePlan
  I->>O: DeploymentManifest
  O->>A: Deploy IaC
  A-->>O: Success/Fail
  O->>S: Seed Data
  S-->>V: Environment
  V-->>U: Ready notice
```


## 4 Data Model

```text
AttackSpec → ResourcePlan → DeploymentManifests → TelemetrySchema -> GraphDB representation
```

## 5 Integration Points

- Microsoft Graph & Entra ID for tenant and identity operations.  
- Azure Resource Manager or Terraform for infrastructure deployment.  
- Microsoft 365 APIs for workload data.  
- Sentinel & Log Analytics for telemetry collection.  

## 6 Testing & Governance

- **Unit & contract tests** executed per micro-service in isolated sandbox.  
- **Canary environments** validated nightly with representative attack library.  
- **Policy guardrails** (Azure Policy, Defender for Cloud) enforced pre-merge.  

