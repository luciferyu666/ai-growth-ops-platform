# ADR-0011: Notification Provider Adapter, Retry Policy, and Alert Thresholds

## Status

Accepted

## Context

MVP-006 introduced a notification outbox, background job ledger, and operational events.

The next step is to make notification delivery replaceable, retryable, and observable without coupling product workflows to a specific vendor or sending real external messages during local demos.

## Decision

Add a notification provider adapter boundary.

The backend selects a provider through `NOTIFICATION_PROVIDER`. The default provider is `mock`, which simulates delivery and deterministic failure modes for tests and demos. A `console` provider is also available for local logging. Real email or messaging providers must be added as explicit adapters with provider-specific secrets, compliance review, and webhook handling.

Add retry scheduling to the existing outbox/job state machine:

- `pending` -> `processing` -> `delivered`
- `pending` -> `processing` -> `retry_scheduled`
- `retry_scheduled` -> `processing` -> `delivered`
- `retry_scheduled` -> `processing` -> `dead_letter`

Background jobs mirror this state using `queued`, `running`, `retry_scheduled`, `succeeded`, and `dead_letter`.

Use `notification_outbox.next_attempt_at` and `background_jobs.next_run_at` to control due work. Retry delay uses exponential backoff from `NOTIFICATION_RETRY_BASE_SECONDS`, capped by `NOTIFICATION_RETRY_MAX_SECONDS`.

Add operations alert evaluation:

- Dead-letter notifications threshold.
- Failed/dead-letter jobs threshold.
- Stalled due notifications threshold based on `NOTIFICATION_ALERT_STALLED_MINUTES`.

Alerts are exposed through `/workspace/operations/alerts` and can be recorded as `operational_events` through `/workspace/operations/alerts/evaluate` or automatic dead-letter processing.

## Consequences

- The workflow can demonstrate delivery success, retry scheduling, and dead-letter escalation without external side effects.
- Provider integration work has a stable adapter boundary.
- Operators can see alert summaries in the workspace UI.
- The system still does not send real outbound email or platform messages by default.
- Provider webhook ingestion remains a future integration task.

## Follow-Up Work

- Add a production email provider adapter after vendor and compliance approval.
- Add provider webhook ingestion for delivery, bounce, and complaint events.
- Add notification templates and localization.
- Add alert resolution policy and external observability integrations.
