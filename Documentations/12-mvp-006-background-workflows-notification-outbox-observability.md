# MVP-006: Background Workflow Jobs, Notification Outbox, and Operational Observability

## Purpose

MVP-006 adds the operational foundation needed before external integrations are introduced.

The goal is to prove that the platform can queue work, persist notification intent, process jobs, and show operational status from the UI and API.

## Delivered Scope

- `notification_outbox` table for persisted notification intent and delivery status.
- `background_jobs` table for queued/running/succeeded/failed job records.
- `operational_events` table for observable workflow lifecycle events.
- Celery task `app.worker.process_notification_job`.
- Inline processing endpoint for deterministic local demos.
- Workspace APIs for outbox, jobs, and operational event listing.
- Workspace API for queueing review notifications.
- Frontend Operations panel in `/workspace`.
- Structured FastAPI request logging middleware.

## API Surface

Operations:

- `GET /workspace/notification-outbox`
- `GET /workspace/background-jobs`
- `GET /workspace/operational-events`
- `POST /workspace/workflows/review-notification`
- `POST /workspace/background-jobs/process-pending`
- `POST /workspace/background-jobs/{job_id}/dispatch`

The default UI uses `process-pending` so demos do not depend on race timing with the worker. The Celery dispatch endpoint is available for queue-based execution.

## Data Model

New tables:

- `notification_outbox`
- `background_jobs`
- `operational_events`

The outbox records channel, recipient, subject, body, status, attempts, provider message ID, error, and metadata.

The job ledger records job type, queue, status, Celery task ID, attempts, actor, resource reference, and execution timestamps.

Operational events record severity, component, event type, message, correlation ID, resource reference, and metadata.

## Delivery Boundary

MVP-006 uses `mock-notification-provider`.

This intentionally does not send real email or messages. Real delivery providers must be added later as explicit adapters with provider-specific configuration, retries, webhook handling, and compliance review.

## Acceptance Criteria

- `alembic upgrade head` creates the three operations tables.
- Owner/admin/operator can queue review notification workflows.
- Reviewer/viewer cannot run workflow jobs.
- Queueing creates a notification outbox record, background job, audit event, and operational events.
- Processing pending jobs marks the notification delivered and job succeeded.
- Operational events show started, delivered, and succeeded lifecycle records.
- `/workspace` displays outbox, jobs, and operational events.
- `npm run check` passes.
- `npm run web:build` passes.
- `npm run api:lint` passes.
- `npm run api:test` passes.
- `alembic check` reports no schema drift.

## Not Included

- Real email delivery.
- Provider webhook ingestion.
- Scheduled retries.
- Dead-letter queues.
- Alerting integrations.
- External observability drain configuration.

## Recommended Next Milestone

`MVP-007: Notification Provider Adapter + Retry Policy + Alert Thresholds`

This should connect the outbox to a real provider in a controlled way, add retry scheduling, and introduce alert thresholds for failed or stalled workflows.
