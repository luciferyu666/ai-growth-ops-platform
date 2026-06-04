# MVP-003: RBAC + Review Queue + Policy-Gated Content Workflow

## Purpose

MVP-003 turns the workspace demo into a more credible SaaS operating workflow. It separates content creation from content approval, adds role-based permissions, and prevents policy-blocked drafts from being approved.

The goal is not to implement production identity or a full workflow engine yet. The goal is to prove the platform can enforce business rules in the backend while presenting a simple operator-facing workflow in the frontend.

## Implemented Scope

### RBAC Foundation

RBAC is implemented in `apps/api/app/services/rbac.py`.

Roles:

- `owner`: full workspace access
- `admin`: full workspace access
- `operator`: create CRM records, consent records, and content drafts
- `reviewer`: read workspace data and approve/reject content
- `viewer`: read-only access

The current local demo auth reads `X-Demo-Role`. Production auth can later map verified identity claims into the same role contract.

### Review Queue

Content drafts now enter the workflow as:

```text
pending_review -> approved
pending_review -> rejected
```

New endpoint:

```text
GET /workspace/review-queue
```

The review queue is tenant-scoped and only returns pending drafts for the active workspace.

### Policy-Gated Content Approval

Policy evaluation is implemented in `apps/api/app/services/content_policy.py`.

Policy results are stored under:

```text
content_drafts.model_metadata.policy
```

Approval requires:

- role permission: `content.review`
- draft status: `pending_review`
- policy status: `passed`

Policy-blocked drafts remain visible in the review queue but cannot be approved.

### Frontend Demo

`/workspace` now supports:

- workspace switching
- role switching
- review queue display
- policy status display
- blocked sample creation
- approval/rejection action testing

## Demo Flow

1. Open `http://localhost:3000/workspace`.
2. Reset demo data as `Owner`.
3. Switch role to `Operator`.
4. Create a compliant mock draft.
5. Try to approve it as `Operator`; backend returns permission denied.
6. Switch role to `Reviewer`.
7. Approve the pending draft.
8. Create a blocked sample.
9. Try to approve it as `Reviewer` or `Owner`; backend blocks approval because policy failed.
10. Inspect audit events for created, policy evaluated, approved, and rejected actions.

## Acceptance Criteria

- Operators can create drafts but cannot approve or reject.
- Reviewers can approve pending policy-passed drafts.
- Policy-blocked drafts cannot be approved.
- Review queue shows pending drafts for the active workspace only.
- Audit events include policy evaluation and approval/rejection actions.
- Frontend can demonstrate role switching and policy status.
- API tests cover RBAC denial, reviewer approval, and blocked policy approval.

## What Is Still Not Included

- Production login provider.
- Persisted custom role definitions.
- Full permission admin UI.
- Pagination for list endpoints.
- Update/delete workflows with audit events.
- Immutable policy and approval snapshots.
- Real LLM provider policy evaluation.

## Recommended Next Milestone

`MVP-004: Pagination + Update/Delete Audit + Production Auth Decision`

This should harden the platform for larger demo datasets and prepare the project for a production authentication provider.
