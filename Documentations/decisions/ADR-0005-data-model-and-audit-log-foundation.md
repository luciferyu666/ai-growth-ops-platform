# ADR-0005: Data Model and Audit Log Foundation

## Status

Accepted

## Date

2026-06-03

## Context

The initial scaffold can run the web app, API, worker, PostgreSQL, and Redis, but the backend did not yet use persistent storage.

The platform needs a durable foundation for CRM-style records, consent tracking, AI-generated content review, and compliance auditability before product features are added.

## Decision

Use SQLAlchemy 2.x with Alembic-managed PostgreSQL migrations.

The API must not create tables automatically on startup. Schema changes must go through Alembic migrations.

The initial schema includes:

- `organizations`
- `contacts`
- `consent_records`
- `content_drafts`
- `approval_records`
- `audit_events`

The API exposes:

- `/health`: lightweight service configuration health
- `/health/deep`: database and Redis connectivity health

## Initial Data Model

### Organizations

Represents a company or customer account. It is the parent for contacts and generated content drafts.

Key fields:

- `name`
- `legal_name`
- `domain`
- `industry`
- `status`
- `metadata`

### Contacts

Represents a person associated with an organization.

Key fields:

- `organization_id`
- `name`
- `email`
- `phone`
- `role`
- `source`
- `metadata`

### Consent Records

Tracks channel-level consent and lawful basis for contact workflows.

Key fields:

- `contact_id`
- `channel`
- `status`
- `lawful_basis`
- `source`
- `granted_at`
- `revoked_at`
- `metadata`

Each contact can have one consent record per channel.

### Content Drafts

Stores AI-assisted content before approval or publishing.

Key fields:

- `organization_id`
- `title`
- `channel`
- `status`
- `prompt_version`
- `prompt_text`
- `draft_text`
- `model_name`
- `model_metadata`
- `created_by_actor`
- `metadata`

### Approval Records

Stores review decisions for content drafts.

Key fields:

- `content_draft_id`
- `decision`
- `reviewer_actor`
- `comment`
- `decided_at`
- `metadata`

### Audit Events

Stores compliance and operational events across high-risk workflows.

Key fields:

- `action`
- `actor_id`
- `actor_type`
- `resource_type`
- `resource_id`
- `source`
- `request_id`
- `metadata`
- `created_at`

Audit events intentionally avoid strict foreign keys so they can record attempts, failures, deleted resources, external provider callbacks, and future auth-provider actors.

## Rationale

PostgreSQL gives the project reliable relational constraints, indexing, JSONB fields for extensible metadata, and a strong migration path.

SQLAlchemy keeps backend domain code in Python, which fits the selected FastAPI and AI/data workflow stack.

Alembic is required from the start because implicit table creation would make schema drift likely and would be unsafe for long-running AI-assisted development.

The audit log is intentionally introduced before auth, LLM providers, or CRM workflows. Any future feature that touches messaging, generated content, consent, approval, data import, or external platform integration should emit audit events.

## Consequences

- Developers must run `alembic upgrade head` after schema changes.
- Future model changes must include explicit migrations.
- Auth is still deferred, so `actor_id` and `actor_type` are string fields for now.
- Audit events are append-oriented and should not be used as the main query model for product screens.
- JSONB `metadata` fields are available for controlled extension, but core query fields should be modeled as columns when they become stable.

## Validation Criteria

- `alembic upgrade head` succeeds.
- PostgreSQL shows the initial six domain tables plus Alembic version tracking.
- `/health` returns `status: ok`.
- `/health/deep` returns healthy database and Redis checks.
- Backend tests cover lightweight health, deep health, and a basic DB session query.

## Follow-Up Decisions

- ADR-0004: Authentication and authorization approach
- ADR-0006: LLM provider abstraction and prompt audit design
- ADR-0007: Local development environment hardening
- ADR-0008: Domain service boundaries for CRM, content, approval, and audit workflows
