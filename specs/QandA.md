| Turn # | Speaker | Message |
|-------|---------|---------|
| 1 | BA | Can SimBuilder simulate cross-tenant attacks involving lateral movement, or is it limited to single-tenant scenarios in the MVP? |
| 2 | PO | MVP supports single-tenant, but the Planner and data models already store tenantId arrays; Phase 2 will enable automated multi-tenant topologies and lateral paths. |
| 3 | BA | Which user roles will operate the platform and how will RBAC separate their privileges and audit actions? |
| 4 | PO | Two roles are defined: SimulationRequester (trigger and clean up simulations) and PlatformAdmin (manage catalogs and policies); custom Azure AD roles enforce least privilege with activity logs streamed to Sentinel. |
| 5 | BA | What mechanisms cap budget during long-running simulations to prevent runaway Azure spend? |
| 6 | PO | Planner tags every resource with costCenter, ttlHours, and owner; a nightly FinOps function queries Cost Management, alerts at 80 % of budget, and auto-decommissions environments exceeding limits. |
| 7 | BA | If the IaC deployment partially fails, do we support automatic rollback and state cleanup? |
| 8 | PO | Orchestrator groups resources per simulation; on error it triggers `az deployment group delete`, replays the last good manifest, and records the incident in the audit log. |
| 9 | BA | How do we create realistic identity graphs and mail traffic without handling real PII? |
| 10 | PO | DataSeeder uses Faker generators and domain templates; only synthetic data is stored, and nightly privacy scans verify no real PII is introduced. |
| 11 | BA | How is telemetry completeness validated to ensure every attack step is observable? |
| 12 | PO | Validator compares Sentinel and Log Analytics events against the expected TelemetrySchema; missing or delayed signals mark the environment unhealthy and halt hand-off. |
| 13 | BA | Will external plugins be able to add AWS support in Phase 3, and what contract must they satisfy? |
| 14 | PO | Plugin SDK exposes a `ProviderInterface` with plan(), deploy(), seed(); plugins must pass contract tests and publish a signed SBOM before registry acceptance. |
| 15 | BA | What encryption and secret management standards cover credentials used by agents and seeded accounts? |
| 16 | PO | Agents leverage Managed Identities for runtime tokens; any persistent secrets reside in Key Vault with customer-managed keys, and seeded passwords rotate post-deploy through Graph API. |
| 17 | BA | What scale testing proves the non-functional requirement of supporting 10+ concurrent full-scale simulations? |
| 18 | PO | CI load pipeline provisions 12 tenants in parallel using the attack library, ensuring 95th percentile deploy time is under 30 minutes with <5 % failure rate. |
| 19 | BA | The roadmap mentions a web UI; what accessibility commitments will it meet? |
| 20 | PO | The UI will adopt Fluent UI components, comply with WCAG 2.1 AA, and run automated axe-core scans plus manual keyboard testing in release gates. |