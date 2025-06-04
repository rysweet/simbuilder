# Orchestrator Agent Specification

## Purpose / Overview
Coordinates the entire simulation deployment workflow, manages resource provisioning, monitors deployment progress, and handles rollback scenarios. Serves as the central coordinator for all deployment activities.

## Functional Requirements / User Stories
- Orchestrate multi-step deployment workflows
- Coordinate with IaC providers (Terraform, ARM/Bicep)
- Monitor deployment progress and handle failures
- Manage resource cleanup and rollback procedures

## Dependencies
- InfraSynthesis Agent (deployment manifests)
- Terraform Runner and ARM/Bicep Runner
- Service Bus (workflow coordination)
- FinOps Alerting (cost monitoring)

## Acceptance Criteria
- Successfully orchestrate complex multi-resource deployments
- Handle deployment failures with proper rollback
- Complete deployments within expected timeframes
- Provide real-time progress updates

## Open Questions
- Deployment orchestration strategy for complex dependencies?
- Rollback procedures and state management?
- Integration with multiple IaC providers?