# ADR-0007: RBAC, Review Queue, and Policy-Gated Content

## Status

Accepted

## Context

MVP-002 established workspace ownership and a replaceable auth context. The next risk is allowing every authenticated workspace member to perform every action. For a credible SaaS workflow, content creation and content approval must be separated, and approval must be blocked when policy checks fail.

The system is still a technical proposal demo, so a full workflow engine, authorization framework, or policy service would be premature.

## Decision

Implement MVP-003 with service-level RBAC, a lightweight review queue, and a deterministic local policy gate.

- RBAC is implemented in `app/services/rbac.py`.
- Demo roles are resolved from `X-Demo-Role`.
- Supported roles:
  - `owner`
  - `admin`
  - `operator`
  - `reviewer`
  - `viewer`
- Content drafts are created with `status = pending_review`.
- `GET /workspace/review-queue` lists pending drafts for the active workspace.
- Policy evaluation is implemented in `app/services/content_policy.py`.
- Policy results are stored in `content_drafts.model_metadata.policy`.
- Approval requires:
  - `content.review` permission
  - `status = pending_review`
  - `policy.status = passed`
- Rejection requires:
  - `content.review` permission
  - `status = pending_review`
- Every policy and approval action writes an audit event.

## Consequences

- Operators can create CRM records and submit drafts, but cannot approve them.
- Reviewers can approve or reject pending drafts without CRM write access.
- Blocked policy drafts remain visible in the review queue but cannot be approved.
- The backend now has a clear authorization boundary before production auth is selected.
- The policy engine is deterministic and local; it is not a replacement for a full Trust & Safety system.

## Follow-Up Decisions

- Decide whether RBAC should be stored in database policies or external auth claims.
- Add update/delete workflows with audit events.
- Add pagination and filtering to workspace list endpoints.
- Split policy evaluation into a dedicated workflow step when real LLM providers are introduced.
- Add immutable approval snapshots for production compliance.
