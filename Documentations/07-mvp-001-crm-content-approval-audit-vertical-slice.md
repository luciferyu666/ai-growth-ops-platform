# MVP-001: CRM + Content Approval + Audit Event Vertical Slice

## Purpose

`MVP-001` turns the technical proposal demo into a working vertical slice.

It proves that the project can connect:

`Organization -> Contact -> Consent -> Content Draft -> Approval -> Audit Event`

This is still not a full production product. It is a controlled MVP workflow for demonstrating delivery capability, compliant product direction, and full-stack integration.

## Implemented Scope

### Backend APIs

Implemented under `/workspace`:

- `GET /workspace/metrics`
- `GET /workspace/organizations`
- `POST /workspace/organizations`
- `GET /workspace/contacts`
- `POST /workspace/contacts`
- `GET /workspace/consent-records`
- `POST /workspace/consent-records`
- `GET /workspace/content-drafts`
- `POST /workspace/content-drafts`
- `GET /workspace/approval-records`
- `POST /workspace/content-drafts/{content_draft_id}/approve`
- `POST /workspace/content-drafts/{content_draft_id}/reject`
- `GET /workspace/audit-events`
- `POST /workspace/demo/reset`

### Mock AI Provider

The backend includes a local mock AI content service.

It creates a compliant content draft and stores:

- `prompt_version`
- `prompt_text`
- `draft_text`
- `model_name`
- `model_metadata`

This avoids external LLM dependency during the demo while preserving the future AI workflow contract.

### Audit Logging

The following mutation actions create audit events:

- `organization.created`
- `contact.created`
- `consent_record.created`
- `consent_record.updated`
- `content_draft.created`
- `content_draft.approved`
- `content_draft.rejected`

### Frontend Workflow

Implemented at:

`http://localhost:3000/workspace`

The page supports:

- Reset demo data
- Refresh workspace data
- Create organization
- Create contact
- Grant email consent
- Generate mock AI content draft
- Approve latest draft
- Display metrics
- Display records
- Display audit events

The main dashboard also reads real metrics from:

`GET /workspace/metrics`

## Demo Flow

Recommended live demo:

1. Open `http://localhost:3000/workspace`.
2. Click `Reset demo data`.
3. Show non-zero metrics.
4. Create a new organization.
5. Create a contact for the organization.
6. Grant consent.
7. Generate a mock AI content draft.
8. Approve the latest draft.
9. Show audit events.
10. Return to `http://localhost:3000` and show dashboard metrics.

## Value Demonstrated

This milestone proves:

- Frontend/backend integration
- PostgreSQL persistence
- Domain API design
- Mock AI workflow boundary
- Human approval workflow
- Mutation audit trail
- Dashboard metrics from API data
- Repeatable demo data setup

## What Is Still Not Included

This milestone does not include:

- Authentication
- Role-based permissions
- Multi-tenant workspace model
- Real LLM provider integration
- External CRM integrations
- External review platform integrations
- Production deployment
- Billing
- Advanced reporting

## Acceptance Criteria

Accepted when:

- Backend tests pass
- Workspace APIs appear in FastAPI docs
- `POST /workspace/demo/reset` creates non-zero demo metrics
- Browser can complete the vertical slice from the UI
- Audit events appear after mutations
- Dashboard metrics are read from the API

## Recommended Next Milestone

`MVP-002: Auth + Workspace Ownership + Service Layer Hardening`

Suggested scope:

- Add service classes for domain logic
- Add authentication provider decision
- Add workspace/tenant model
- Add actor identity from authenticated user
- Add API pagination
- Add update/delete workflows with audit events
