# SimBuilder Overview

## 1  Purpose & Scope (What)

SimBuilder automates the planning, provisioning, and clean-up of **enterprise-grade cloud simulation environments** purpose-built to **replay sophisticated cyber-attacks at scale**. Security researchers, red teams, and product engineers can obtain an isolated Azure tenant, populated identities, realistic data, and the telemetry wiring needed to measure detection quality – all with a single prompt.

### 1.1 End-to-End Flow

```text
 ┌──────────────────────────┐
 │  User Attack Description │
 └──────────┬───────────────┘
            ▼
  Clarifier Agent – collects missing details
            ▼
  Resource Planner – drafts tenant/infra plan
            ▼
  User Review & Adjustments (optional)
            ▼
  IaC Generator – emits Bicep / Terraform
            ▼
  Orchestrator – deploys to Azure
            ▼
  Data Seeder – populates datasets & links
            ▼
  Validator – replays attack preconditions
            ▼
  Hand-off: ready environment for testing
```

### 1.2 Key Functional Capabilities

- **Interactive requirements capture** through incremental clarifying questions.  
- **AI-driven resource planning** of tenants, identities, networks, workloads, and datasets.  
- **Generation of IaC artifacts** such as Bicep, Terraform, or ARM templates with built-in rollback.  
- **Data seeding** that establishes cross-tenant and cross-workload relationships to mirror real production graphs.  
- **Precondition validation** ensuring the environment can support the attack sequence and collect all relevant telemetry.  
- **Versioning and repeatability** via Git-based manifests, with automated clean-up and **cost control** tags.  

### 1.3 Non-Functional Requirements

| Quality Attribute | Target |
|-------------------|--------|
| Security | Principle of least privilege, encrypted secrets, RBAC audit logs |
| Scalability | Support 10+ concurrent full-scale simulations |
| Auditability | Immutable build artifacts, signed releases, provenance tracking |
| Extensibility | Plugin catalog for new cloud providers or attack patterns |
| Cost Governance | Budget caps, TTL auto-teardown, FinOps alerting at 80 % spend |
| Accessibility | Web UI meets WCAG 2.1 AA & keyboard-only navigation |

## 2  Implementation Approach (How)

### 2.1 Multi-Agent Architecture

| Agent | Responsibility |
|-------|---------------|
| **PlannerAgent** | Convert high-level attack spec to concrete `ResourcePlan` |
| **InfraSynthesisAgent** | Transform plan into IaC `DeploymentManifest` |
| **DataSeeder** | Generate synthetic identities, mail, files, and logs |
| **Validator** | Ensure deployed state matches prerequisites & telemetry expectations |
| **Orchestrator** | Coordinate workflow via message bus and persist state |

```text
 LLM ↔ Knowledge Base ↔ Constraint Solver → IaC Emitter
```

### 2.2 Technology Choices

- **Cloud**: Azure subscription & Azure Kubernetes Service.  
- **CI/CD**: GitHub Actions & Azure DevOps pipelines for gated deploys.  
- **Runtime**: Python micro-services, FastAPI, Azure Functions (durable for long-running ops).  
- **AI**: OpenAI GPT-4 & Azure AI Search for pattern retrieval.  
- **Messaging**: Azure Service Bus topic for agent events.  

### 2.3 Core Data Model

```text
AttackSpec → ResourcePlan → DeploymentManifest → TelemetrySchema
```

### 2.4 Integration Points

- Microsoft Graph & Entra ID for tenant and identity operations.  
- Azure Resource Manager for infrastructure deployment.  
- Microsoft 365 APIs for workload data.  
- Sentinel & Log Analytics for telemetry collection.  

### 2.5 Testing, CI, and Governance

- **Unit & contract tests** executed per micro-service in isolated sandbox.  
- **Canary environments** validated nightly with representative attack library.  
- **Policy guardrails** (Azure Policy, Defender for Cloud) enforced pre-merge.  

### 2.6 Roadmap

1. **MVP** – single-tenant simulations, manual trigger, limited attack library.
2. **Phase 2** – multi-tenant and lateral-movement support, plugin SDK implementing `ProviderInterface`, cost dashboards, self-service API.
3. **Phase 3** – Web UI (WCAG 2.1 AA), multi-cloud expansion (AWS, GCP), public attack marketplace & analytics.

### 2.7 Acceptance Criteria

- All IaC deployments pass policy guardrails with zero critical violations.
- Telemetry validator confirms 100 % coverage for each library attack.
- 95th percentile end-to-end deployment time under **30 minutes** for **12** parallel simulations.
- Budget alert triggers at **80 %** and auto-clean-up at **100 %** of limit.
- UI axe-core automation reports **0 critical accessibility issues** on release.

---