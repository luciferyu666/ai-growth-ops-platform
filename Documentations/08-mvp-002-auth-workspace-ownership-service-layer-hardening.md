# MVP-002: Auth + Workspace Ownership + Service Layer Hardening

## Purpose

MVP-002 upgrades the previous CRM/content approval demo from a single global dataset into a SaaS-shaped vertical slice. The goal is to prove that operators, workspaces, CRM records, generated drafts, approvals, and audit events can be owned and isolated by workspace.

This milestone intentionally does not select a production auth vendor. Instead, it creates the replaceable backend auth boundary that a production provider will later plug into.

## Implemented Scope

### Demo Auth Context

- Added persisted identity tables:
  - `users`
  - `workspaces`
  - `workspace_memberships`
- Added `GET /workspace/auth/context`.
- Added header-based demo auth for local development:
  - `X-Demo-User-Email`
  - `X-Demo-User-Name`
  - `X-Demo-Workspace-Slug`
  - `X-Demo-Workspace-Name`
- The API resolves headers into a stable `AuthContext`.

### Workspace Ownership

- Added `workspace_id` to:
  - `organizations`
  - `contacts`
  - `consent_records`
  - `content_drafts`
  - `approval_records`
  - `audit_events`
- Existing demo data is backfilled into `demo-growth-ops`.
- All workspace API reads and mutations are scoped by current `AuthContext.workspace_id`.
- `POST /workspace/demo/reset` now resets only the active workspace.

### Audit Hardening

- Mutation actor identity now comes from `AuthContext.actor_id`.
- The client no longer controls audit actor identity through request payloads.
- Every audit event includes `workspace_id`.

### Service Layer Hardening

- Added `app/services/auth.py` for auth context resolution.
- Added `app/services/workspace_data.py` for workspace-scoped guards and metrics.
- Centralized 404 access checks for workspace-owned records.

### Frontend Demo

- `/workspace` now displays:
  - current demo user
  - current workspace slug
  - membership role
  - active tenant-scoped metrics
- Added workspace switching between:
  - `demo-growth-ops`
  - `demo-sandbox`
- All frontend API calls include the active demo auth headers.

## Demo Flow

1. Open `http://localhost:3000/workspace`.
2. Confirm the auth context panel shows the active actor and workspace.
3. Reset demo data in `Primary`.
4. Create an organization, contact, consent record, content draft, and approval.
5. Switch to `Sandbox`.
6. Confirm the dataset changes because metrics and records are scoped by workspace.
7. Reset or create sandbox data without affecting primary workspace data.
8. Inspect audit events and confirm actor/workspace attribution.

## Value Demonstrated

- SaaS workspace ownership foundation.
- Tenant-scoped backend API behavior.
- Replaceable auth boundary for future Clerk/Auth0/Azure Entra/OIDC integration.
- Audit trail attribution that does not trust client-supplied actor data.
- Frontend-to-backend integration using real API calls and PostgreSQL persistence.

## What Is Still Not Included

- Production login UI.
- External identity provider.
- Full RBAC policy enforcement.
- Organization invitation flow.
- Passwords or session cookies.
- Billing account ownership.
- Deployment-level secret rotation.

## Acceptance Criteria

- `alembic upgrade head` creates workspace ownership schema.
- `GET /workspace/auth/context` returns user, workspace, membership, and role.
- Workspace metrics are scoped by `X-Demo-Workspace-Slug`.
- A record created in one workspace is not visible from another workspace.
- Cross-workspace references return `404`.
- Mutation audit actor comes from auth context.
- `/workspace` can switch between demo workspaces.
- API tests cover tenant isolation.

## Recommended Next Milestone

`MVP-003: RBAC + Review Queue + Policy-Gated Content Workflow`

Status: implemented. See `Documentations/09-mvp-003-rbac-review-queue-policy-gated-content.md`.
