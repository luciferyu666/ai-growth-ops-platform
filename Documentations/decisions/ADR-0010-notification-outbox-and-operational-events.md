# ADR-0010: Notification Outbox and Operational Events

## Status

Accepted

## Context

MVP-006 adds background workflow execution and operational observability.

The platform needs a reliable way to record notification intent before delivery, process work asynchronously, and expose operational status to operators without coupling product workflows to a specific email or messaging vendor.

## Decision

Use a database-backed notification outbox and background job ledger.

The outbox records notification intent and delivery state. Background jobs record execution state. Operational events record the observable lifecycle of queueing, dispatch, delivery, and failure.

Initial delivery uses a mock notification provider. No real email, SMS, messaging, review-site posting, or external platform delivery is performed in MVP-006.

## Consequences

- Product workflows can enqueue notifications safely before real provider integration.
- Operators can inspect pending notifications, queued jobs, and recent operational events.
- Celery can process jobs through `app.worker.process_notification_job`.
- The API also exposes an inline processor for deterministic local demos and tests.
- Future provider integrations should write to the same outbox state machine rather than bypassing it.

## Follow-Up Work

- Add a real email provider adapter.
- Add retry scheduling and max-attempt escalation.
- Add dead-letter handling.
- Add notification templates.
- Add provider webhook ingestion.
- Add alert thresholds for failed jobs and stalled outbox items.
