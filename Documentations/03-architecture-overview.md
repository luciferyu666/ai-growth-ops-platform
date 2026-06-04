# Architecture Overview

## Current State

The initial technology stack has been selected in `Documentations/decisions/ADR-0002-technology-stack.md`.

The initial repository layout and application scaffold have been accepted in `Documentations/decisions/ADR-0003-repository-layout-and-application-scaffolding.md`.

The initial persistence model and audit log foundation have been accepted in `Documentations/decisions/ADR-0005-data-model-and-audit-log-foundation.md`.

The auth context and workspace ownership foundation has been accepted in `Documentations/decisions/ADR-0006-auth-context-and-workspace-ownership.md`.

The RBAC, review queue, and policy-gated content workflow has been accepted in `Documentations/decisions/ADR-0007-rbac-review-queue-and-policy-gated-content.md`.

The production authentication provider decision has been accepted in `Documentations/decisions/ADR-0008-production-auth-provider.md`.

The auth onboarding and approval snapshot boundaries have been accepted in `Documentations/decisions/ADR-0009-auth-onboarding-and-approval-snapshot-boundaries.md`.

The notification outbox and operational events foundation has been accepted in `Documentations/decisions/ADR-0010-notification-outbox-and-operational-events.md`.

The notification provider adapter, retry policy, and alert thresholds have been accepted in `Documentations/decisions/ADR-0011-notification-provider-retry-and-alert-policy.md`.

## Candidate System Areas

- Next.js web application for operators and administrators
- FastAPI service for workflow orchestration
- Celery worker service for scheduled jobs and background processing
- LLM service layer for prompt execution, evaluation, and audit records
- CRM and data integration layer
- Reporting and monitoring layer
- Auth context and workspace ownership layer
- RBAC and policy-gated review workflow layer
- Paginated SaaS list APIs and audit-backed mutation layer
- Production OIDC authentication layer
- Workspace invitation onboarding layer
- Immutable approval evidence layer
- Notification outbox and background job execution layer
- Operational events and structured request logging layer
- Notification provider adapter and retry/dead-letter workflow layer
- Operations monitor alert threshold layer

## Candidate Data Domains

- Users
- Workspaces
- Workspace memberships
- Workspace invitations
- Organizations
- Contacts
- Consent records
- Campaigns
- Content drafts
- Approval records
- Approval snapshots
- Notification outbox
- Background jobs
- Operational events
- Operation alerts
- Policy evaluations
- Review invitations
- Reputation signals
- Tasks and workflow events
- Audit logs

## Open Architecture Decisions

- Production auth rollout and environment enforcement policy
- Persisted RBAC policy model
- Notification provider webhook ingestion
- Notification template governance
- LLM provider abstraction
- Deployment target
- Observability stack
