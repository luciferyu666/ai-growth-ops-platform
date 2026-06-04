# MVP-007: Notification Provider Adapter, Retry Policy, and Alert Thresholds

## Purpose

MVP-007 upgrades the MVP-006 operations foundation from a simple mock delivery path into a provider-adapter workflow with retry scheduling, dead-letter escalation, and alert visibility.

The goal is to prove the platform can operate like a SaaS workflow system: work is queued, delivery is attempted through a replaceable provider, transient failures are retried, permanent failures are escalated, and operators can see the resulting state.

## Delivered Scope

- Notification provider adapter interface.
- Default `mock` provider for deterministic success, retryable failure, and permanent failure.
- Local `console` provider for non-external logging.
- Provider name persisted on `notification_outbox`.
- `last_attempt_at` on notification outbox records.
- `next_run_at` on background jobs.
- Retry scheduling with configurable exponential backoff.
- Dead-letter status for exhausted or permanent provider failures.
- Alert summary API for dead-letter notifications, failed jobs, and stalled notifications.
- Alert evaluation endpoint that records operational alert events.
- Workspace UI controls for queueing a retry sample, processing jobs, and evaluating alerts.
- Workspace UI display of provider, attempt counts, next retry time, errors, and active alerts.

## API Surface

Operations:

- `GET /workspace/operations/alerts`
- `POST /workspace/operations/alerts/evaluate`

Existing operations endpoints now include provider and retry state:

- `GET /workspace/notification-outbox`
- `GET /workspace/background-jobs`
- `POST /workspace/workflows/review-notification`
- `POST /workspace/background-jobs/process-pending`
- `POST /workspace/background-jobs/{job_id}/dispatch`

## Configuration

Local defaults:

- `NOTIFICATION_PROVIDER=mock`
- `NOTIFICATION_RETRY_BASE_SECONDS=60`
- `NOTIFICATION_RETRY_MAX_SECONDS=3600`
- `NOTIFICATION_ALERT_DEAD_LETTER_THRESHOLD=1`
- `NOTIFICATION_ALERT_FAILED_JOB_THRESHOLD=1`
- `NOTIFICATION_ALERT_STALLED_MINUTES=15`

## Delivery Boundary

MVP-007 still does not send real external messages.

The provider adapter is intentionally present before production provider integration so the team can test workflow behavior, auditability, and operational visibility without side effects.

## Acceptance Criteria

- `alembic upgrade head` adds provider and retry scheduling fields.
- Queueing a review notification records the configured provider.
- Successful processing marks the notification `delivered` and the job `succeeded`.
- Retryable provider failure marks the notification and job `retry_scheduled`.
- Exhausted retries mark the notification and job `dead_letter`.
- Dead-letter processing records operations monitor alert events.
- `/workspace/operations/alerts` returns active alert summaries.
- `/workspace` displays retry/dead-letter/provider/alert status.
- `npm run check` passes.
- `npm run web:build` passes.
- `npm run api:lint` passes.
- `npm run api:test` passes.
- `alembic check` reports no schema drift.

## Not Included

- Real email delivery.
- Provider webhook ingestion.
- Bounce or complaint handling.
- Notification template management.
- External observability drain configuration.

## Recommended Next Milestone

`MVP-008: Notification Templates + Provider Webhooks + Snapshot Export`

This should add template governance, provider callback ingestion, and exportable approval/snapshot evidence before any production messaging provider is enabled.
