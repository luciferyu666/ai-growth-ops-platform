# MVP-004: Pagination, Update/Delete Audit, and Production Auth Decision

## Purpose

MVP-004 upgrades the proposal demo from a basic vertical slice into a more realistic SaaS workflow foundation.

The goal is not to add external integrations yet. The goal is to prove that list views can scale beyond toy data, mutations remain auditable, and the project has a clear production authentication direction before inviting real users.

## Delivered Scope

- Paginated workspace list APIs with `items` and `pagination` metadata.
- Filter support for organizations, contacts, consent records, content drafts, review queue, approval records, and audit events.
- Update and delete mutations for organizations, contacts, and content drafts.
- Audit events for update and delete mutations.
- Frontend list controls for content draft filtering and pagination.
- Frontend demo controls for archive, delete, revise, and delete-draft actions.
- Production auth provider decision captured in `Documentations/decisions/ADR-0008-production-auth-provider.md`.

## Backend Changes

Workspace list endpoints now return a consistent paginated response:

```json
{
  "items": [],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 0,
    "has_next": false,
    "has_previous": false
  }
}
```

The updated API surface includes:

- `GET /workspace/organizations`
- `GET /workspace/contacts`
- `GET /workspace/consent-records`
- `GET /workspace/content-drafts`
- `GET /workspace/review-queue`
- `GET /workspace/approval-records`
- `GET /workspace/audit-events`
- `PATCH /workspace/organizations/{organization_id}`
- `DELETE /workspace/organizations/{organization_id}`
- `PATCH /workspace/contacts/{contact_id}`
- `DELETE /workspace/contacts/{contact_id}`
- `PATCH /workspace/content-drafts/{content_draft_id}`
- `DELETE /workspace/content-drafts/{content_draft_id}`

Every update and delete mutation writes an audit event with actor, workspace, resource, action, metadata, and timestamp attribution.

## Frontend Changes

The workspace demo now reads paginated API responses and exposes visible list controls for content drafts:

- Status filter: all, pending review, approved, rejected.
- Previous / next page controls.
- Result range and total count display.
- Operator-facing actions for archive, contact deletion, draft revision, and draft deletion.

This gives the demo a clearer product story: the system is not just showing static proposal screens; it can manage records, revise content, enforce review policy, and preserve mutation history.

## Production Auth Decision

Auth0 by Okta is selected as the first production authentication provider.

The decision keeps the current domain API contract stable:

- Next.js handles login/session using Auth0's Next.js integration.
- FastAPI validates bearer JWTs for protected API routes.
- The backend continues to own workspace membership and effective RBAC roles.
- Local `X-Demo-*` header auth remains available only for development and proposal demos.

Microsoft Entra ID remains a future enterprise SSO option, especially for Azure-heavy customers.

## Acceptance Criteria

- Workspace list endpoints return `items` and `pagination`.
- List endpoints support scoped filters without leaking records across workspaces.
- Update and delete mutations write audit events.
- Frontend dashboard still loads real API data.
- Frontend workspace demo exposes pagination and update/delete controls.
- `npm run check` passes.
- `npm run web:build` passes.
- `npm run api:lint` passes.
- `npm run api:test` passes.
- `alembic check` reports no pending schema drift.

## Not Included

- External Auth0 login implementation.
- Workspace invitation UI.
- Immutable approval snapshot storage.
- Real LLM provider integration.
- External platform publishing or messaging integrations.

These remain intentionally deferred. They depend on production auth, invitation flow, and stricter review/audit guarantees.

## Recommended Next Milestone

`MVP-005: Production Auth Integration + Workspace Invitations + Immutable Review Snapshots`

This should implement the Auth0 decision, add invite-based workspace onboarding, and persist immutable review snapshots so future approval records can prove exactly what content, policy result, prompt metadata, and reviewer decision were accepted.
