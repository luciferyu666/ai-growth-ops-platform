# MVP-005: Production Auth Integration, Workspace Invitations, and Approval Snapshots

## Purpose

MVP-005 upgrades the SaaS foundation from local demo ownership into a production-ready onboarding and review evidence model.

The goal is to prove that the platform can validate production identity, onboard users into tenant workspaces through invitations, and preserve immutable approval evidence for human-reviewed AI content.

## Delivered Scope

- Auth provider switch through `AUTH_PROVIDER`.
- Local default remains `demo-header`.
- Auth0 mode validates bearer JWTs with issuer, audience, signature, and expiration checks.
- Next.js Auth0 SDK added with a lazy `Auth0Client`.
- Next.js `proxy.ts` wired for Auth0 mode while staying inactive in local demo mode.
- Workspace invitation create, list, and accept APIs.
- Invitation acceptance creates or updates `workspace_memberships`.
- Approval decisions create immutable `approval_snapshots`.
- Workspace UI exposes invitation creation, local invite acceptance, pending invitation counts, and snapshot cards.
- Alembic migration adds `workspace_invitations` and `approval_snapshots`.

## API Surface

Authentication:

- `GET /workspace/auth/context`
- Production mode expects `Authorization: Bearer <jwt>` and `X-Workspace-Slug`.

Workspace invitations:

- `GET /workspace/invitations`
- `POST /workspace/invitations`
- `POST /workspace/invitations/accept`

Approval snapshots:

- `GET /workspace/approval-snapshots`

Existing approve and reject endpoints now create snapshots:

- `POST /workspace/content-drafts/{content_draft_id}/approve`
- `POST /workspace/content-drafts/{content_draft_id}/reject`

## Data Model

New tables:

- `workspace_invitations`
- `approval_snapshots`

`workspace_invitations` stores the invitee email, role, status, token hash, inviter actor, acceptance metadata, and expiration.

`approval_snapshots` stores a JSON evidence package containing the reviewed draft, policy result, approval record, and reviewer context. The raw invitation token is returned only once when creating an invitation; only its hash is stored.

## Auth Rollout Boundary

Auth0 integration is implemented as a configurable production path, but this repo does not include tenant secrets.

To enable Auth0 in a deployed environment:

```text
AUTH_PROVIDER=auth0
NEXT_PUBLIC_AUTH_PROVIDER=auth0
AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_SECRET=
AUTH0_SCOPE=openid profile email
APP_BASE_URL=
```

The backend expects the access token to contain an email claim. If the Auth0 API access token does not include email by default, add a namespaced custom claim for email and keep the backend mapping explicit.

## Acceptance Criteria

- `alembic upgrade head` creates invitation and snapshot tables.
- `GET /workspace/auth/context` still works with local demo headers.
- `AUTH_PROVIDER=auth0` without a bearer token returns `401`.
- Owner can create a workspace invitation.
- Operator cannot create a workspace invitation.
- Invitee can accept an invitation and receive a workspace membership.
- Approval and rejection decisions create approval snapshots.
- Snapshots preserve reviewed draft text after later draft edits.
- `/workspace` displays invitation and snapshot data from the API.
- `npm run check` passes.
- `npm run web:build` passes.
- `npm run api:lint` passes.
- `npm run api:test` passes.
- `alembic check` reports no schema drift.

## Not Included

- Auth0 tenant provisioning.
- Real user email delivery for invitations.
- Invitation revoke/resend endpoints.
- Dedicated snapshot detail page.
- Production CI policy blocking `demo-header`.
- Full persisted RBAC policy editor.

## Recommended Next Milestone

`MVP-006: Background Workflow Jobs + Notification Outbox + Operational Observability`

This should add durable workflow execution for invitation delivery, content review notifications, audit exports, and system health monitoring before introducing external CRM or messaging integrations.
