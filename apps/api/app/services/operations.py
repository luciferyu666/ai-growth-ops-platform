from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    BackgroundJob,
    ContentDraft,
    NotificationOutbox,
    OperationalEvent,
)
from app.services.notification_providers import (
    NotificationPayload,
    get_notification_provider,
)

NOTIFICATION_JOB_TYPE = "notification.dispatch"
FINAL_NOTIFICATION_STATUSES = {"delivered", "dead_letter"}
RETRYABLE_JOB_STATUSES = {"queued", "retry_scheduled"}
ALERT_DEAD_LETTER_NOTIFICATIONS = "dead_letter_notifications"
ALERT_FAILED_JOBS = "failed_jobs"
ALERT_STALLED_NOTIFICATIONS = "stalled_notifications"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _safe_max_attempts(metadata: dict | None) -> int:
    raw_value = (metadata or {}).get("max_attempts", 3)
    try:
        return min(max(int(raw_value), 1), 10)
    except (TypeError, ValueError):
        return 3


def _retry_delay(attempt_count: int) -> timedelta:
    settings = get_settings()
    base_seconds = max(settings.notification_retry_base_seconds, 0)
    max_seconds = max(settings.notification_retry_max_seconds, base_seconds)
    if base_seconds == 0:
        return timedelta(seconds=0)

    retry_power = max(attempt_count - 1, 0)
    return timedelta(seconds=min(base_seconds * (2**retry_power), max_seconds))


def _merge_notification_metadata(
    notification: NotificationOutbox,
    metadata: dict,
) -> None:
    notification.extra_data = {
        **notification.extra_data,
        **metadata,
    }


def record_operational_event(
    session: Session,
    *,
    workspace_id: UUID,
    event_type: str,
    component: str,
    message: str,
    severity: str = "info",
    status: str = "open",
    correlation_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> OperationalEvent:
    event = OperationalEvent(
        workspace_id=workspace_id,
        severity=severity,
        component=component,
        event_type=event_type,
        message=message,
        status=status,
        correlation_id=correlation_id,
        resource_type=resource_type,
        resource_id=resource_id,
        extra_data=metadata or {},
    )
    session.add(event)
    return event


def queue_review_notification(
    session: Session,
    *,
    workspace_id: UUID,
    content_draft: ContentDraft,
    recipient: str,
    subject: str,
    body: str,
    actor_id: str,
    metadata: dict | None = None,
) -> tuple[NotificationOutbox, BackgroundJob]:
    correlation_id = str(uuid4())
    provider = get_notification_provider()
    now = utc_now()
    notification = NotificationOutbox(
        workspace_id=workspace_id,
        channel="email",
        recipient=recipient.strip().lower(),
        subject=subject,
        body=body,
        provider_name=provider.name,
        status="pending",
        max_attempts=_safe_max_attempts(metadata),
        next_attempt_at=now,
        idempotency_key=f"review-notification:{content_draft.id}:{correlation_id}",
        extra_data={
            **(metadata or {}),
            "content_draft_id": str(content_draft.id),
            "correlation_id": correlation_id,
            "provider": provider.name,
        },
    )
    session.add(notification)
    session.flush()

    job = BackgroundJob(
        workspace_id=workspace_id,
        job_type=NOTIFICATION_JOB_TYPE,
        queue_name="notifications",
        status="queued",
        resource_type="notification_outbox",
        resource_id=str(notification.id),
        created_by_actor=actor_id,
        next_run_at=now,
        extra_data={
            "notification_outbox_id": str(notification.id),
            "content_draft_id": str(content_draft.id),
            "correlation_id": correlation_id,
        },
    )
    session.add(job)
    session.flush()

    record_operational_event(
        session,
        workspace_id=workspace_id,
        event_type="notification.queued",
        component="notification_outbox",
        message=f"Queued notification for {notification.recipient}",
        correlation_id=correlation_id,
        resource_type="notification_outbox",
        resource_id=str(notification.id),
        metadata={
            "job_id": str(job.id),
            "channel": notification.channel,
            "provider": notification.provider_name,
            "max_attempts": notification.max_attempts,
        },
    )
    record_operational_event(
        session,
        workspace_id=workspace_id,
        event_type="background_job.queued",
        component="worker",
        message=f"Queued {job.job_type}",
        correlation_id=correlation_id,
        resource_type="background_job",
        resource_id=str(job.id),
        metadata={"queue_name": job.queue_name},
    )
    return notification, job


def get_background_job_or_404(
    session: Session,
    *,
    workspace_id: UUID,
    job_id: UUID,
) -> BackgroundJob:
    job = session.scalar(
        select(BackgroundJob).where(
            BackgroundJob.id == job_id,
            BackgroundJob.workspace_id == workspace_id,
        )
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Background job not found")
    return job


def _notification_for_job(
    session: Session,
    job: BackgroundJob,
) -> NotificationOutbox:
    notification_id = job.extra_data.get("notification_outbox_id") or job.resource_id
    if not notification_id:
        raise HTTPException(status_code=409, detail="Job has no notification target")
    try:
        parsed_notification_id = UUID(str(notification_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail="Job notification target is invalid",
        ) from exc

    notification = session.scalar(
        select(NotificationOutbox).where(
            NotificationOutbox.id == parsed_notification_id,
            NotificationOutbox.workspace_id == job.workspace_id,
        )
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


def process_notification_job(
    session: Session,
    *,
    job: BackgroundJob,
) -> tuple[NotificationOutbox, BackgroundJob]:
    if job.job_type != NOTIFICATION_JOB_TYPE:
        raise HTTPException(status_code=409, detail="Unsupported job type")

    notification = _notification_for_job(session, job)
    if job.status == "succeeded" or notification.status in FINAL_NOTIFICATION_STATUSES:
        return notification, job

    correlation_id = (
        job.extra_data.get("correlation_id")
        or notification.extra_data.get("correlation_id")
        or str(job.id)
    )
    now = utc_now()
    if job.next_run_at and job.next_run_at > now:
        return notification, job

    job.status = "running"
    job.started_at = now
    job.attempts += 1
    job.next_run_at = None
    notification.status = "processing"
    notification.attempt_count += 1
    notification.last_attempt_at = now

    record_operational_event(
        session,
        workspace_id=job.workspace_id,
        event_type="background_job.started",
        component="worker",
        message=f"Started {job.job_type}",
        correlation_id=correlation_id,
        resource_type="background_job",
        resource_id=str(job.id),
        metadata={
            "attempt": job.attempts,
            "provider": notification.provider_name,
        },
    )

    provider = get_notification_provider(notification.provider_name)
    result = provider.send(
        NotificationPayload(
            channel=notification.channel,
            recipient=notification.recipient,
            subject=notification.subject,
            body=notification.body,
            metadata={
                **notification.extra_data,
                "notification_id": str(notification.id),
                "attempt": notification.attempt_count,
            },
        )
    )

    if not result.success:
        error_message = result.error_message or "Notification provider failed"
        _merge_notification_metadata(
            notification,
            {
                "provider": provider.name,
                "provider_result": result.metadata,
                "last_error_retryable": result.retryable,
            },
        )

        retry_allowed = (
            result.retryable and notification.attempt_count < notification.max_attempts
        )
        if retry_allowed:
            next_attempt_at = now + _retry_delay(notification.attempt_count)
            notification.status = "retry_scheduled"
            notification.next_attempt_at = next_attempt_at
            notification.error_message = error_message
            job.status = "retry_scheduled"
            job.next_run_at = next_attempt_at
            job.error_message = error_message
            record_operational_event(
                session,
                workspace_id=job.workspace_id,
                event_type="notification.retry_scheduled",
                component="notification_outbox",
                message=f"Scheduled retry for {notification.recipient}",
                severity="warning",
                correlation_id=correlation_id,
                resource_type="notification_outbox",
                resource_id=str(notification.id),
                metadata={
                    "job_id": str(job.id),
                    "attempt": notification.attempt_count,
                    "max_attempts": notification.max_attempts,
                    "next_attempt_at": _iso(next_attempt_at),
                    "provider": provider.name,
                },
            )
            record_operational_event(
                session,
                workspace_id=job.workspace_id,
                event_type="background_job.retry_scheduled",
                component="worker",
                message=f"Scheduled retry for {job.job_type}",
                severity="warning",
                correlation_id=correlation_id,
                resource_type="background_job",
                resource_id=str(job.id),
                metadata={
                    "error_message": error_message,
                    "next_run_at": _iso(next_attempt_at),
                    "attempt": job.attempts,
                },
            )
            return notification, job

        now = utc_now()
        job.status = "dead_letter"
        job.finished_at = now
        job.next_run_at = None
        job.error_message = error_message
        notification.status = "dead_letter"
        notification.failed_at = now
        notification.next_attempt_at = None
        notification.error_message = error_message
        record_operational_event(
            session,
            workspace_id=job.workspace_id,
            event_type="notification.dead_letter",
            component="notification_outbox",
            message=error_message,
            severity="error",
            correlation_id=correlation_id,
            resource_type="notification_outbox",
            resource_id=str(notification.id),
            metadata={
                "job_id": str(job.id),
                "recipient": notification.recipient,
                "attempt": notification.attempt_count,
                "max_attempts": notification.max_attempts,
                "provider": provider.name,
                "retryable": result.retryable,
            },
        )
        record_operational_event(
            session,
            workspace_id=job.workspace_id,
            event_type="background_job.dead_letter",
            component="worker",
            message=f"Moved {job.job_type} to dead letter",
            severity="error",
            correlation_id=correlation_id,
            resource_type="background_job",
            resource_id=str(job.id),
            metadata={"error_message": error_message},
        )
        evaluate_workspace_operation_alerts(
            session,
            workspace_id=job.workspace_id,
            record_events=True,
        )
        return notification, job

    provider_message_id = result.provider_message_id or f"{provider.name}-{notification.id}"
    notification.status = "delivered"
    notification.sent_at = utc_now()
    notification.next_attempt_at = None
    notification.failed_at = None
    notification.provider_message_id = provider_message_id
    notification.error_message = None
    _merge_notification_metadata(
        notification,
        {
            "provider": provider.name,
            "provider_result": result.metadata,
            "last_error_retryable": None,
        },
    )
    job.status = "succeeded"
    job.finished_at = notification.sent_at
    job.next_run_at = None
    job.error_message = None

    record_operational_event(
        session,
        workspace_id=job.workspace_id,
        event_type="notification.delivered",
        component="notification_outbox",
        message=f"Delivered notification to {notification.recipient}",
        status="resolved",
        correlation_id=correlation_id,
        resource_type="notification_outbox",
        resource_id=str(notification.id),
        metadata={
            "job_id": str(job.id),
            "provider_message_id": provider_message_id,
            "provider": provider.name,
        },
    )
    record_operational_event(
        session,
        workspace_id=job.workspace_id,
        event_type="background_job.succeeded",
        component="worker",
        message=f"Completed {job.job_type}",
        status="resolved",
        correlation_id=correlation_id,
        resource_type="background_job",
        resource_id=str(job.id),
        metadata={"attempts": job.attempts},
    )
    return notification, job


def process_pending_notification_jobs(
    session: Session,
    *,
    workspace_id: UUID,
    limit: int,
) -> list[tuple[NotificationOutbox, BackgroundJob]]:
    now = utc_now()
    jobs = session.scalars(
        select(BackgroundJob)
        .where(
            BackgroundJob.workspace_id == workspace_id,
            BackgroundJob.job_type == NOTIFICATION_JOB_TYPE,
            BackgroundJob.status.in_(RETRYABLE_JOB_STATUSES),
            or_(BackgroundJob.next_run_at.is_(None), BackgroundJob.next_run_at <= now),
        )
        .order_by(
            BackgroundJob.next_run_at.asc().nullsfirst(),
            BackgroundJob.created_at.asc(),
        )
        .limit(limit)
    ).all()
    return [process_notification_job(session, job=job) for job in jobs]


def _count_scalar(session: Session, statement) -> int:
    return session.scalar(statement) or 0


def _alert_event_exists(
    session: Session,
    *,
    workspace_id: UUID,
    event_type: str,
) -> bool:
    existing_event = session.scalar(
        select(OperationalEvent.id)
        .where(
            OperationalEvent.workspace_id == workspace_id,
            OperationalEvent.component == "operations_monitor",
            OperationalEvent.event_type == event_type,
            OperationalEvent.status == "open",
        )
        .limit(1)
    )
    return existing_event is not None


def _record_alert_event_if_needed(
    session: Session,
    *,
    workspace_id: UUID,
    alert: dict,
) -> None:
    event_type = f"operations.alert.{alert['code']}"
    if _alert_event_exists(
        session,
        workspace_id=workspace_id,
        event_type=event_type,
    ):
        return

    record_operational_event(
        session,
        workspace_id=workspace_id,
        event_type=event_type,
        component="operations_monitor",
        message=alert["message"],
        severity=alert["severity"],
        metadata={
            "count": alert["count"],
            "threshold": alert["threshold"],
            "code": alert["code"],
        },
    )


def evaluate_workspace_operation_alerts(
    session: Session,
    *,
    workspace_id: UUID,
    record_events: bool = False,
) -> dict:
    session.flush()
    settings = get_settings()
    now = utc_now()
    stalled_cutoff = now - timedelta(
        minutes=max(settings.notification_alert_stalled_minutes, 0)
    )
    dead_letter_count = _count_scalar(
        session,
        select(func.count(NotificationOutbox.id)).where(
            NotificationOutbox.workspace_id == workspace_id,
            NotificationOutbox.status == "dead_letter",
        ),
    )
    retry_scheduled_count = _count_scalar(
        session,
        select(func.count(NotificationOutbox.id)).where(
            NotificationOutbox.workspace_id == workspace_id,
            NotificationOutbox.status == "retry_scheduled",
        ),
    )
    failed_job_count = _count_scalar(
        session,
        select(func.count(BackgroundJob.id)).where(
            BackgroundJob.workspace_id == workspace_id,
            BackgroundJob.status.in_(("failed", "dead_letter")),
        ),
    )
    stalled_notification_count = _count_scalar(
        session,
        select(func.count(NotificationOutbox.id)).where(
            NotificationOutbox.workspace_id == workspace_id,
            NotificationOutbox.status.in_(("pending", "processing", "retry_scheduled")),
            NotificationOutbox.created_at <= stalled_cutoff,
            or_(
                NotificationOutbox.next_attempt_at.is_(None),
                NotificationOutbox.next_attempt_at <= now,
            ),
        ),
    )
    open_alert_event_count = _count_scalar(
        session,
        select(func.count(OperationalEvent.id)).where(
            OperationalEvent.workspace_id == workspace_id,
            OperationalEvent.component == "operations_monitor",
            OperationalEvent.status == "open",
            OperationalEvent.severity.in_(("warning", "error")),
        ),
    )

    thresholds = {
        ALERT_DEAD_LETTER_NOTIFICATIONS: (
            settings.notification_alert_dead_letter_threshold
        ),
        ALERT_FAILED_JOBS: settings.notification_alert_failed_job_threshold,
        ALERT_STALLED_NOTIFICATIONS: 1,
        "stalled_minutes": settings.notification_alert_stalled_minutes,
    }
    counts = {
        ALERT_DEAD_LETTER_NOTIFICATIONS: dead_letter_count,
        "retry_scheduled_notifications": retry_scheduled_count,
        ALERT_FAILED_JOBS: failed_job_count,
        ALERT_STALLED_NOTIFICATIONS: stalled_notification_count,
        "open_alert_events": open_alert_event_count,
    }
    alerts: list[dict] = []

    if dead_letter_count >= settings.notification_alert_dead_letter_threshold:
        alerts.append(
            {
                "code": ALERT_DEAD_LETTER_NOTIFICATIONS,
                "severity": "error",
                "message": "Dead-letter notifications reached the alert threshold.",
                "count": dead_letter_count,
                "threshold": settings.notification_alert_dead_letter_threshold,
            }
        )
    if failed_job_count >= settings.notification_alert_failed_job_threshold:
        alerts.append(
            {
                "code": ALERT_FAILED_JOBS,
                "severity": "error",
                "message": "Failed jobs reached the alert threshold.",
                "count": failed_job_count,
                "threshold": settings.notification_alert_failed_job_threshold,
            }
        )
    if stalled_notification_count >= 1:
        alerts.append(
            {
                "code": ALERT_STALLED_NOTIFICATIONS,
                "severity": "warning",
                "message": "Due notifications are stalled past the configured window.",
                "count": stalled_notification_count,
                "threshold": 1,
            }
        )

    if record_events:
        for alert in alerts:
            _record_alert_event_if_needed(
                session,
                workspace_id=workspace_id,
                alert=alert,
            )

    return {
        "provider": get_settings().notification_provider,
        "thresholds": thresholds,
        "counts": counts,
        "alerts": alerts,
        "generated_at": _iso(now),
    }
