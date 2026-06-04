# ADR-0009: Auth Onboarding and Approval Snapshot Boundaries

## Status

Accepted

## Context

MVP-005 introduces production-auth wiring, workspace invitations, and immutable approval snapshots.

The platform needs two clear boundaries before external users or real review workflows are added:

- Authenticated identity is not the same as workspace membership.
- Approval history must preserve what was reviewed, even if a draft is later edited or deleted.

## Decision

In production Auth0 mode, the backend validates bearer JWTs but does not automatically create workspace memberships.

Workspace membership must be created by accepting a pending workspace invitation. The backend remains the source of truth for effective role and workspace access through `workspace_memberships`.

Approval decisions create an `approval_snapshots` record that stores the reviewed draft text, prompt metadata, model metadata, policy result, reviewer context, and approval decision as JSON evidence.

`approval_snapshots.content_draft_id` stores the original draft UUID but intentionally does not enforce a foreign key to `content_drafts`. This keeps the evidence record available even if the mutable draft record is later removed.

## Consequences

- Auth0 can prove identity, but SaaS authorization remains internal and tenant-scoped.
- Invitation acceptance becomes the onboarding control point.
- Local `demo-header` auth can still create demo workspaces automatically for proposal demos and tests.
- Approval records can be queried through mutable workflow tables, while snapshots preserve the reviewed evidence.
- Future retention policies must handle snapshots as compliance evidence, not ordinary editable content.

## Follow-Up Work

- Add email delivery for invitations.
- Add invitation revocation and resend endpoints.
- Add production enforcement that disables `demo-header` outside local development.
- Add snapshot retention and export policies.
- Add reviewer-visible snapshot detail pages.
