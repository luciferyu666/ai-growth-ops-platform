# Roadmap

## Phase 0 - Workspace Foundation

- Initialize repository structure
- Define project charter
- Define compliance boundaries
- Define Codex collaboration conventions

## Phase 1 - Product Discovery

- Define user roles
- Define first target industry
- Define MVP workflows
- Define data sources and authorization basis
- Draft initial domain model

## Phase 2 - MVP Implementation

- Build operator dashboard
- Implement organization and contact management
- Implement content drafting workflow
- Implement human approval flow
- Implement audit log foundation

## Recommended Next Milestone - MVP-001

- Build Organization CRUD
- Build Contact CRUD
- Build Consent Record workflow
- Build Content Draft workflow with a mock AI provider
- Build Approval / Rejection workflow
- Write Audit Events for every mutation
- Connect Dashboard metrics to API data
- Add seed demo data for proposal demonstrations

Status: implemented as a first vertical slice. See `Documentations/07-mvp-001-crm-content-approval-audit-vertical-slice.md`.

## Recommended Next Milestone - MVP-002

- Add local demo auth context
- Add workspace / tenant ownership model
- Add `users`, `workspaces`, and `workspace_memberships`
- Scope domain records and audit events by `workspace_id`
- Move access guards and metrics into backend services
- Replace client-supplied actor strings with auth-context actor identity
- Add frontend workspace switching for tenant isolation demonstrations

Status: implemented as the SaaS ownership foundation. See `Documentations/08-mvp-002-auth-workspace-ownership-service-layer-hardening.md`.

## Recommended Next Milestone - MVP-003

- Add role-based access control policy checks
- Add review queue states and filters
- Add policy-gated content approval actions
- Add frontend role switching for permission demonstrations
- Add policy-blocked draft demonstration

Status: implemented as a policy-gated review workflow. See `Documentations/09-mvp-003-rbac-review-queue-policy-gated-content.md`.

## Recommended Next Milestone - MVP-004

- Add pagination and filtering for list endpoints
- Add update and delete workflows with audit events
- Add production authentication provider decision

Status: implemented as the first scalable SaaS list and mutation-audit hardening pass. See `Documentations/10-mvp-004-pagination-update-delete-production-auth.md` and `Documentations/decisions/ADR-0008-production-auth-provider.md`.

## Recommended Next Milestone - MVP-005

- Implement Auth0 login, logout, callback, and session handling
- Replace production API auth with bearer JWT validation
- Keep demo header auth development-only
- Add workspace invitation and membership acceptance flow
- Add immutable approval and policy snapshots
- Add token claim mapping tests

Status: implemented as the production-auth wiring, workspace invitation, and approval evidence foundation. See `Documentations/11-mvp-005-production-auth-invitations-approval-snapshots.md` and `Documentations/decisions/ADR-0009-auth-onboarding-and-approval-snapshot-boundaries.md`.

## Recommended Next Milestone - MVP-006

- Add background workflow jobs for invitation delivery
- Add notification outbox table and worker execution
- Add review notification events
- Add operational event dashboard
- Add snapshot export endpoint
- Add production auth environment guardrails

Status: implemented as a background workflow, notification outbox, and operational observability foundation. See `Documentations/12-mvp-006-background-workflows-notification-outbox-observability.md` and `Documentations/decisions/ADR-0010-notification-outbox-and-operational-events.md`.

## Recommended Next Milestone - MVP-007

- Add notification provider adapter boundary
- Add retry scheduling and max-attempt handling
- Add dead-letter status and escalation events
- Add alert thresholds for failed jobs and stalled notifications

Status: implemented as a provider-adapter, retry/dead-letter, and alert threshold foundation. See `Documentations/13-mvp-007-notification-provider-retry-alert-thresholds.md` and `Documentations/decisions/ADR-0011-notification-provider-retry-and-alert-policy.md`.

## Recommended Next Milestone - MVP-008

- Add notification template governance
- Add provider webhook ingestion for delivery, bounce, and complaint events
- Add approval snapshot export endpoint
- Add operations alert resolution policy
- Add production provider readiness checks

## Phase 3 - Integrations

- Add CRM import/export
- Add official messaging provider integration
- Add official review platform management integrations where available
- Add reporting and monitoring

## Phase 4 - Scale and Operations

- Add queue-based background workers
- Add role-based permissions
- Add workflow analytics
- Add deployment automation
- Add production observability
