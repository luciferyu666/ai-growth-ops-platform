# ADR-0006: Auth Context and Workspace Ownership Foundation

## Status

Accepted

## Context

The MVP workspace demo now needs to move from a single global dataset to a SaaS-shaped model where records belong to a workspace and mutations are attributed to an authenticated actor.

Choosing a production authentication provider too early would couple the prototype to deployment, billing, user provisioning, and RBAC decisions that are not yet settled. The project still needs an executable auth boundary so backend services, audit events, and frontend workflows can be built against the right contract.

## Decision

Implement a local demo auth context as the MVP-002 authentication seam.

- The API accepts local development headers:
  - `X-Demo-User-Email`
  - `X-Demo-User-Name`
  - `X-Demo-Workspace-Slug`
  - `X-Demo-Workspace-Name`
- The backend resolves those headers into persisted records:
  - `users`
  - `workspaces`
  - `workspace_memberships`
- The backend returns an `AuthContext` containing actor, user, workspace, membership, role, and auth mode.
- Domain mutations derive `actor_id` from `AuthContext`; the client no longer controls audit actor identity.
- All CRM, consent, content, approval, and audit records are scoped by `workspace_id`.
- Production auth can later replace the auth dependency without changing the domain API contract.

## Consequences

- The current demo can prove tenant-scoped SaaS behavior before external auth is selected.
- Tests can verify workspace isolation with deterministic headers.
- Audit events now include both actor and workspace scope.
- This is not production authentication. It is a local development seam and must be replaced with a verified session or token provider before external users access the system.

## Follow-Up Decisions

- Select production auth provider: Clerk, Auth0, Azure Entra ID, or self-managed OIDC.
- Define RBAC policy per role and operation.
- Decide whether audit logs should remain after workspace deletion or cascade with workspace data.
- Add row-level authorization checks to non-workspace routes when those routes become tenant-owned.
