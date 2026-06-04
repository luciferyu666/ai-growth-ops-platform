from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import (
    ApprovalRecord,
    ApprovalSnapshot,
    AuditEvent,
    BackgroundJob,
    ConsentRecord,
    Contact,
    ContentDraft,
    NotificationOutbox,
    Organization,
    OperationalEvent,
    WorkspaceInvitation,
)
from app.services.approval_snapshots import create_approval_snapshot
from app.services.auth import (
    AuthContext,
    IdentityContext,
    get_auth_context,
    get_identity_context,
)
from app.services.audit import record_audit_event
from app.services.content_policy import (
    ensure_policy_allows_approval,
    ensure_reviewable_status,
    evaluate_content_policy,
    policy_result_from_draft,
)
from app.services.mock_ai import generate_mock_content_draft
from app.services.invitations import (
    accept_workspace_invitation,
    create_workspace_invitation,
)
from app.services.operations import (
    evaluate_workspace_operation_alerts,
    get_background_job_or_404,
    process_pending_notification_jobs,
    queue_review_notification,
    record_operational_event,
)
from app.services.rbac import (
    CONSENT_WRITE,
    CONTENT_CREATE,
    CONTENT_REVIEW,
    CONTENT_REVIEW_QUEUE_READ,
    CONTENT_WRITE,
    CRM_WRITE,
    DEMO_RESET,
    OPERATIONS_RUN,
    WORKSPACE_INVITE,
    WORKSPACE_READ,
    require_permission,
)
from app.worker import process_notification_job_task
from app.services.workspace_data import (
    delete_workspace_records,
    get_contact_or_404,
    get_content_draft_or_404,
    get_organization_or_404,
    get_workspace_metrics as calculate_workspace_metrics,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = None
    domain: str | None = None
    industry: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = None
    domain: str | None = None
    industry: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class ContactCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    source: str | None = "demo"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    source: str | None = None
    metadata: dict[str, Any] | None = None


class ConsentRecordCreate(BaseModel):
    contact_id: UUID
    channel: str = Field(min_length=1, max_length=80)
    status: str = "granted"
    lawful_basis: str | None = "consent"
    source: str | None = "demo"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContentDraftCreate(BaseModel):
    organization_id: UUID
    title: str = Field(min_length=1, max_length=255)
    channel: str = "email"
    prompt_text: str | None = None
    draft_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContentDraftUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    channel: str | None = None
    prompt_text: str | None = None
    draft_text: str | None = None
    metadata: dict[str, Any] | None = None


class ApprovalDecisionCreate(BaseModel):
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkspaceInvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: str = "viewer"
    expires_in_days: int = Field(default=7, ge=1, le=90)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkspaceInvitationAccept(BaseModel):
    token: str = Field(min_length=16, max_length=255)


class ReviewNotificationCreate(BaseModel):
    content_draft_id: UUID
    recipient: str = Field(default="reviewer@ai-growth-ops.local", max_length=320)
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _organization_dict(organization: Organization) -> dict[str, Any]:
    return {
        "id": str(organization.id),
        "workspace_id": str(organization.workspace_id),
        "name": organization.name,
        "legal_name": organization.legal_name,
        "domain": organization.domain,
        "industry": organization.industry,
        "status": organization.status,
        "metadata": organization.extra_data,
        "created_at": _iso(organization.created_at),
        "updated_at": _iso(organization.updated_at),
    }


def _contact_dict(contact: Contact) -> dict[str, Any]:
    return {
        "id": str(contact.id),
        "workspace_id": str(contact.workspace_id),
        "organization_id": str(contact.organization_id),
        "name": contact.name,
        "email": contact.email,
        "phone": contact.phone,
        "role": contact.role,
        "source": contact.source,
        "metadata": contact.extra_data,
        "created_at": _iso(contact.created_at),
        "updated_at": _iso(contact.updated_at),
    }


def _consent_record_dict(consent_record: ConsentRecord) -> dict[str, Any]:
    return {
        "id": str(consent_record.id),
        "workspace_id": str(consent_record.workspace_id),
        "contact_id": str(consent_record.contact_id),
        "channel": consent_record.channel,
        "status": consent_record.status,
        "lawful_basis": consent_record.lawful_basis,
        "source": consent_record.source,
        "granted_at": _iso(consent_record.granted_at),
        "revoked_at": _iso(consent_record.revoked_at),
        "metadata": consent_record.extra_data,
        "created_at": _iso(consent_record.created_at),
        "updated_at": _iso(consent_record.updated_at),
    }


def _content_draft_dict(content_draft: ContentDraft) -> dict[str, Any]:
    policy = policy_result_from_draft(content_draft)
    return {
        "id": str(content_draft.id),
        "workspace_id": str(content_draft.workspace_id),
        "organization_id": str(content_draft.organization_id),
        "title": content_draft.title,
        "channel": content_draft.channel,
        "status": content_draft.status,
        "prompt_version": content_draft.prompt_version,
        "prompt_text": content_draft.prompt_text,
        "draft_text": content_draft.draft_text,
        "model_name": content_draft.model_name,
        "model_metadata": content_draft.model_metadata,
        "policy": policy,
        "created_by_actor": content_draft.created_by_actor,
        "metadata": content_draft.extra_data,
        "created_at": _iso(content_draft.created_at),
        "updated_at": _iso(content_draft.updated_at),
    }


def _approval_record_dict(approval_record: ApprovalRecord) -> dict[str, Any]:
    return {
        "id": str(approval_record.id),
        "workspace_id": str(approval_record.workspace_id),
        "content_draft_id": str(approval_record.content_draft_id),
        "decision": approval_record.decision,
        "reviewer_actor": approval_record.reviewer_actor,
        "comment": approval_record.comment,
        "decided_at": _iso(approval_record.decided_at),
        "metadata": approval_record.extra_data,
        "created_at": _iso(approval_record.created_at),
        "updated_at": _iso(approval_record.updated_at),
    }


def _approval_snapshot_dict(approval_snapshot: ApprovalSnapshot) -> dict[str, Any]:
    return {
        "id": str(approval_snapshot.id),
        "workspace_id": str(approval_snapshot.workspace_id),
        "approval_record_id": (
            str(approval_snapshot.approval_record_id)
            if approval_snapshot.approval_record_id
            else None
        ),
        "content_draft_id": str(approval_snapshot.content_draft_id),
        "decision": approval_snapshot.decision,
        "reviewer_actor": approval_snapshot.reviewer_actor,
        "snapshot_version": approval_snapshot.snapshot_version,
        "snapshot_data": approval_snapshot.snapshot_data,
        "created_at": _iso(approval_snapshot.created_at),
    }


def _workspace_invitation_dict(
    invitation: WorkspaceInvitation,
    *,
    token: str | None = None,
) -> dict[str, Any]:
    payload = {
        "id": str(invitation.id),
        "workspace_id": str(invitation.workspace_id),
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "invited_by_actor": invitation.invited_by_actor,
        "accepted_by_user_id": (
            str(invitation.accepted_by_user_id)
            if invitation.accepted_by_user_id
            else None
        ),
        "accepted_at": _iso(invitation.accepted_at),
        "expires_at": _iso(invitation.expires_at),
        "metadata": invitation.extra_data,
        "created_at": _iso(invitation.created_at),
        "updated_at": _iso(invitation.updated_at),
    }
    if token:
        payload["token"] = token
    return payload


def _notification_outbox_dict(notification: NotificationOutbox) -> dict[str, Any]:
    return {
        "id": str(notification.id),
        "workspace_id": str(notification.workspace_id),
        "channel": notification.channel,
        "recipient": notification.recipient,
        "subject": notification.subject,
        "body": notification.body,
        "provider_name": notification.provider_name,
        "status": notification.status,
        "attempt_count": notification.attempt_count,
        "max_attempts": notification.max_attempts,
        "next_attempt_at": _iso(notification.next_attempt_at),
        "last_attempt_at": _iso(notification.last_attempt_at),
        "sent_at": _iso(notification.sent_at),
        "failed_at": _iso(notification.failed_at),
        "provider_message_id": notification.provider_message_id,
        "error_message": notification.error_message,
        "idempotency_key": notification.idempotency_key,
        "metadata": notification.extra_data,
        "created_at": _iso(notification.created_at),
        "updated_at": _iso(notification.updated_at),
    }


def _background_job_dict(job: BackgroundJob) -> dict[str, Any]:
    return {
        "id": str(job.id),
        "workspace_id": str(job.workspace_id),
        "job_type": job.job_type,
        "queue_name": job.queue_name,
        "status": job.status,
        "celery_task_id": job.celery_task_id,
        "resource_type": job.resource_type,
        "resource_id": job.resource_id,
        "created_by_actor": job.created_by_actor,
        "attempts": job.attempts,
        "next_run_at": _iso(job.next_run_at),
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "error_message": job.error_message,
        "metadata": job.extra_data,
        "created_at": _iso(job.created_at),
        "updated_at": _iso(job.updated_at),
    }


def _operational_event_dict(event: OperationalEvent) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "workspace_id": str(event.workspace_id),
        "severity": event.severity,
        "component": event.component,
        "event_type": event.event_type,
        "message": event.message,
        "status": event.status,
        "correlation_id": event.correlation_id,
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "metadata": event.extra_data,
        "created_at": _iso(event.created_at),
    }


def _membership_dict(membership: Any) -> dict[str, Any]:
    return {
        "id": str(membership.id),
        "workspace_id": str(membership.workspace_id),
        "user_id": str(membership.user_id),
        "role": membership.role,
        "status": membership.status,
        "metadata": membership.extra_data,
        "created_at": _iso(membership.created_at),
        "updated_at": _iso(membership.updated_at),
    }


def _audit_event_dict(audit_event: AuditEvent) -> dict[str, Any]:
    return {
        "id": str(audit_event.id),
        "workspace_id": str(audit_event.workspace_id),
        "action": audit_event.action,
        "actor_id": audit_event.actor_id,
        "actor_type": audit_event.actor_type,
        "resource_type": audit_event.resource_type,
        "resource_id": audit_event.resource_id,
        "source": audit_event.source,
        "request_id": audit_event.request_id,
        "metadata": audit_event.extra_data,
        "created_at": _iso(audit_event.created_at),
    }


def _auth_context_dict(auth: AuthContext) -> dict[str, Any]:
    return {
        "auth_mode": auth.auth_mode,
        "actor_id": auth.actor_id,
        "user": {
            "id": str(auth.user_id),
            "email": auth.user_email,
            "display_name": auth.user_display_name,
        },
        "workspace": {
            "id": str(auth.workspace_id),
            "slug": auth.workspace_slug,
            "name": auth.workspace_name,
        },
        "membership": {
            "id": str(auth.membership_id),
            "role": auth.role,
        },
    }


def _count_for_statement(session: Session, statement: Any) -> int:
    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )
    return session.scalar(count_statement) or 0


def _page_response(
    *,
    items: list[dict[str, Any]],
    total: int,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    return {
        "items": items,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_next": offset + len(items) < total,
            "has_previous": offset > 0,
        },
    }


def _paginated_list(
    *,
    session: Session,
    statement: Any,
    serializer: Any,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    total = _count_for_statement(session, statement)
    records = session.scalars(statement.limit(limit).offset(offset)).all()
    return _page_response(
        items=[serializer(record) for record in records],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/auth/context")
def get_current_auth_context(
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    return _auth_context_dict(auth)


@router.get("/invitations")
def list_workspace_invitations(
    status: str | None = Query(default=None, max_length=50),
    email: str | None = Query(default=None, max_length=320),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_INVITE)
    statement = (
        select(WorkspaceInvitation)
        .where(WorkspaceInvitation.workspace_id == auth.workspace_id)
        .order_by(WorkspaceInvitation.created_at.desc())
    )
    if status:
        statement = statement.where(WorkspaceInvitation.status == status)
    if email:
        statement = statement.where(WorkspaceInvitation.email == email.strip().lower())
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_workspace_invitation_dict,
        limit=limit,
        offset=offset,
    )


@router.post("/invitations", status_code=201)
def create_invitation(
    payload: WorkspaceInvitationCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_INVITE)
    invitation, token = create_workspace_invitation(
        session,
        workspace_id=auth.workspace_id,
        email=payload.email,
        role=payload.role,
        invited_by_actor=auth.actor_id,
        expires_in_days=payload.expires_in_days,
        metadata=payload.metadata,
    )
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="workspace_invitation.created",
        actor_id=auth.actor_id,
        resource_type="workspace_invitation",
        resource_id=str(invitation.id),
        metadata={
            "email": invitation.email,
            "role": invitation.role,
            "expires_at": _iso(invitation.expires_at),
        },
    )
    session.commit()
    session.refresh(invitation)
    return _workspace_invitation_dict(invitation, token=token)


@router.post("/invitations/accept", status_code=201)
def accept_invitation(
    payload: WorkspaceInvitationAccept,
    session: Session = Depends(get_session),
    identity: IdentityContext = Depends(get_identity_context),
) -> dict[str, Any]:
    acceptance = accept_workspace_invitation(
        session,
        token=payload.token,
        identity=identity,
    )
    session.flush()
    record_audit_event(
        session,
        workspace_id=acceptance.invitation.workspace_id,
        action="workspace_invitation.accepted",
        actor_id=identity.actor_id,
        resource_type="workspace_invitation",
        resource_id=str(acceptance.invitation.id),
        metadata={
            "membership_id": str(acceptance.membership.id),
            "membership_created": acceptance.membership_created,
            "role": acceptance.membership.role,
        },
    )
    if acceptance.membership_created:
        record_audit_event(
            session,
            workspace_id=acceptance.invitation.workspace_id,
            action="workspace_membership.created",
            actor_id=identity.actor_id,
            resource_type="workspace_membership",
            resource_id=str(acceptance.membership.id),
            metadata={"invitation_id": str(acceptance.invitation.id)},
        )
    session.commit()
    session.refresh(acceptance.invitation)
    session.refresh(acceptance.membership)
    return {
        "status": "accepted",
        "invitation": _workspace_invitation_dict(acceptance.invitation),
        "membership": _membership_dict(acceptance.membership),
    }


@router.get("/metrics")
def get_workspace_metrics(
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, int]:
    require_permission(auth, WORKSPACE_READ)
    return calculate_workspace_metrics(session, auth.workspace_id)


@router.get("/notification-outbox")
def list_notification_outbox(
    status: str | None = Query(default=None, max_length=50),
    channel: str | None = Query(default=None, max_length=80),
    provider_name: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(NotificationOutbox)
        .where(NotificationOutbox.workspace_id == auth.workspace_id)
        .order_by(NotificationOutbox.created_at.desc())
    )
    if status:
        statement = statement.where(NotificationOutbox.status == status)
    if channel:
        statement = statement.where(NotificationOutbox.channel == channel)
    if provider_name:
        statement = statement.where(NotificationOutbox.provider_name == provider_name)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_notification_outbox_dict,
        limit=limit,
        offset=offset,
    )


@router.get("/background-jobs")
def list_background_jobs(
    status: str | None = Query(default=None, max_length=50),
    job_type: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(BackgroundJob)
        .where(BackgroundJob.workspace_id == auth.workspace_id)
        .order_by(BackgroundJob.created_at.desc())
    )
    if status:
        statement = statement.where(BackgroundJob.status == status)
    if job_type:
        statement = statement.where(BackgroundJob.job_type == job_type)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_background_job_dict,
        limit=limit,
        offset=offset,
    )


@router.get("/operational-events")
def list_operational_events(
    severity: str | None = Query(default=None, max_length=50),
    component: str | None = Query(default=None, max_length=120),
    event_type: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(OperationalEvent)
        .where(OperationalEvent.workspace_id == auth.workspace_id)
        .order_by(OperationalEvent.created_at.desc())
    )
    if severity:
        statement = statement.where(OperationalEvent.severity == severity)
    if component:
        statement = statement.where(OperationalEvent.component == component)
    if event_type:
        statement = statement.where(OperationalEvent.event_type == event_type)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_operational_event_dict,
        limit=limit,
        offset=offset,
    )


@router.get("/operations/alerts")
def get_operation_alerts(
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    return evaluate_workspace_operation_alerts(
        session,
        workspace_id=auth.workspace_id,
        record_events=False,
    )


@router.post("/operations/alerts/evaluate")
def evaluate_operation_alerts(
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, OPERATIONS_RUN)
    alerts = evaluate_workspace_operation_alerts(
        session,
        workspace_id=auth.workspace_id,
        record_events=True,
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="operations.alerts_evaluated",
        actor_id=auth.actor_id,
        resource_type="operational_event",
        metadata={
            "alert_count": len(alerts["alerts"]),
            "role": auth.role,
        },
    )
    session.commit()
    return alerts


@router.post("/workflows/review-notification", status_code=201)
def queue_content_review_notification(
    payload: ReviewNotificationCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, OPERATIONS_RUN)
    content_draft = get_content_draft_or_404(
        session,
        auth.workspace_id,
        payload.content_draft_id,
    )
    subject = payload.subject or f"Review requested: {content_draft.title}"
    body = payload.body or (
        f"{content_draft.title}\n\n"
        f"{content_draft.draft_text}\n\n"
        "Please review this draft in the AI Growth Ops workspace."
    )
    notification, job = queue_review_notification(
        session,
        workspace_id=auth.workspace_id,
        content_draft=content_draft,
        recipient=payload.recipient,
        subject=subject,
        body=body,
        actor_id=auth.actor_id,
        metadata={**payload.metadata, "role": auth.role},
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="workflow.review_notification_queued",
        actor_id=auth.actor_id,
        resource_type="background_job",
        resource_id=str(job.id),
        metadata={
            "notification_outbox_id": str(notification.id),
            "content_draft_id": str(content_draft.id),
            "provider": notification.provider_name,
            "role": auth.role,
        },
    )
    session.commit()
    session.refresh(notification)
    session.refresh(job)
    return {
        "notification": _notification_outbox_dict(notification),
        "job": _background_job_dict(job),
    }


@router.post("/background-jobs/process-pending")
def process_pending_background_jobs(
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, OPERATIONS_RUN)
    processed = process_pending_notification_jobs(
        session,
        workspace_id=auth.workspace_id,
        limit=limit,
    )
    alerts = evaluate_workspace_operation_alerts(
        session,
        workspace_id=auth.workspace_id,
        record_events=True,
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="background_jobs.processed",
        actor_id=auth.actor_id,
        resource_type="background_job",
        metadata={
            "processed_count": len(processed),
            "alert_count": len(alerts["alerts"]),
            "role": auth.role,
        },
    )
    session.commit()
    return {
        "processed_count": len(processed),
        "items": [
            {
                "notification": _notification_outbox_dict(notification),
                "job": _background_job_dict(job),
            }
            for notification, job in processed
        ],
        "alerts": alerts,
    }


@router.post("/background-jobs/{job_id}/dispatch")
def dispatch_background_job(
    job_id: UUID,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, OPERATIONS_RUN)
    job = get_background_job_or_404(
        session,
        workspace_id=auth.workspace_id,
        job_id=job_id,
    )
    async_result = process_notification_job_task.delay(str(job.id))
    job.celery_task_id = async_result.id
    record_operational_event(
        session,
        workspace_id=auth.workspace_id,
        event_type="background_job.dispatched",
        component="worker",
        message=f"Dispatched {job.job_type}",
        correlation_id=job.extra_data.get("correlation_id"),
        resource_type="background_job",
        resource_id=str(job.id),
        metadata={"celery_task_id": async_result.id},
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="background_job.dispatched",
        actor_id=auth.actor_id,
        resource_type="background_job",
        resource_id=str(job.id),
        metadata={"celery_task_id": async_result.id, "role": auth.role},
    )
    session.commit()
    session.refresh(job)
    return _background_job_dict(job)


@router.get("/organizations")
def list_organizations(
    status: str | None = Query(default=None, max_length=50),
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(Organization)
        .where(Organization.workspace_id == auth.workspace_id)
        .order_by(Organization.created_at.desc())
    )
    if status:
        statement = statement.where(Organization.status == status)
    if q:
        pattern = f"%{q}%"
        statement = statement.where(
            or_(
                Organization.name.ilike(pattern),
                Organization.domain.ilike(pattern),
                Organization.industry.ilike(pattern),
            )
        )
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_organization_dict,
        limit=limit,
        offset=offset,
    )


@router.post("/organizations", status_code=201)
def create_organization(
    payload: OrganizationCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CRM_WRITE)
    organization = Organization(
        workspace_id=auth.workspace_id,
        name=payload.name,
        legal_name=payload.legal_name,
        domain=payload.domain,
        industry=payload.industry,
        status=payload.status,
        extra_data=payload.metadata,
    )
    session.add(organization)
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="organization.created",
        actor_id=auth.actor_id,
        resource_type="organization",
        resource_id=str(organization.id),
        metadata={"name": organization.name, "role": auth.role},
    )
    session.commit()
    session.refresh(organization)
    return _organization_dict(organization)


@router.patch("/organizations/{organization_id}")
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CRM_WRITE)
    organization = get_organization_or_404(session, auth.workspace_id, organization_id)
    updates = payload.model_dump(exclude_unset=True)
    changes: dict[str, Any] = {}

    for field, value in updates.items():
        attribute = "extra_data" if field == "metadata" else field
        previous_value = getattr(organization, attribute)
        if previous_value != value:
            setattr(organization, attribute, value)
            changes[field] = {"before": previous_value, "after": value}

    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="organization.updated",
        actor_id=auth.actor_id,
        resource_type="organization",
        resource_id=str(organization.id),
        metadata={"changes": changes, "role": auth.role},
    )
    session.commit()
    session.refresh(organization)
    return _organization_dict(organization)


@router.delete("/organizations/{organization_id}")
def delete_organization(
    organization_id: UUID,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CRM_WRITE)
    organization = get_organization_or_404(session, auth.workspace_id, organization_id)
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="organization.deleted",
        actor_id=auth.actor_id,
        resource_type="organization",
        resource_id=str(organization.id),
        metadata={
            "name": organization.name,
            "domain": organization.domain,
            "role": auth.role,
        },
    )
    session.delete(organization)
    session.commit()
    return {"status": "deleted", "id": str(organization_id)}


@router.get("/contacts")
def list_contacts(
    organization_id: UUID | None = None,
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(Contact)
        .where(Contact.workspace_id == auth.workspace_id)
        .order_by(Contact.created_at.desc())
    )
    if organization_id:
        statement = statement.where(Contact.organization_id == organization_id)
    if q:
        pattern = f"%{q}%"
        statement = statement.where(
            or_(
                Contact.name.ilike(pattern),
                Contact.email.ilike(pattern),
                Contact.role.ilike(pattern),
            )
        )
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_contact_dict,
        limit=limit,
        offset=offset,
    )


@router.post("/contacts", status_code=201)
def create_contact(
    payload: ContactCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CRM_WRITE)
    get_organization_or_404(session, auth.workspace_id, payload.organization_id)
    contact = Contact(
        workspace_id=auth.workspace_id,
        organization_id=payload.organization_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        source=payload.source,
        extra_data=payload.metadata,
    )
    session.add(contact)
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="contact.created",
        actor_id=auth.actor_id,
        resource_type="contact",
        resource_id=str(contact.id),
        metadata={"organization_id": str(payload.organization_id), "role": auth.role},
    )
    session.commit()
    session.refresh(contact)
    return _contact_dict(contact)


@router.patch("/contacts/{contact_id}")
def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CRM_WRITE)
    contact = get_contact_or_404(session, auth.workspace_id, contact_id)
    updates = payload.model_dump(exclude_unset=True)
    changes: dict[str, Any] = {}

    for field, value in updates.items():
        attribute = "extra_data" if field == "metadata" else field
        previous_value = getattr(contact, attribute)
        if previous_value != value:
            setattr(contact, attribute, value)
            changes[field] = {"before": previous_value, "after": value}

    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="contact.updated",
        actor_id=auth.actor_id,
        resource_type="contact",
        resource_id=str(contact.id),
        metadata={"changes": changes, "role": auth.role},
    )
    session.commit()
    session.refresh(contact)
    return _contact_dict(contact)


@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: UUID,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CRM_WRITE)
    contact = get_contact_or_404(session, auth.workspace_id, contact_id)
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="contact.deleted",
        actor_id=auth.actor_id,
        resource_type="contact",
        resource_id=str(contact.id),
        metadata={
            "name": contact.name,
            "email": contact.email,
            "organization_id": str(contact.organization_id),
            "role": auth.role,
        },
    )
    session.delete(contact)
    session.commit()
    return {"status": "deleted", "id": str(contact_id)}


@router.get("/consent-records")
def list_consent_records(
    contact_id: UUID | None = None,
    status: str | None = Query(default=None, max_length=50),
    channel: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(ConsentRecord)
        .where(ConsentRecord.workspace_id == auth.workspace_id)
        .order_by(ConsentRecord.created_at.desc())
    )
    if contact_id:
        statement = statement.where(ConsentRecord.contact_id == contact_id)
    if status:
        statement = statement.where(ConsentRecord.status == status)
    if channel:
        statement = statement.where(ConsentRecord.channel == channel)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_consent_record_dict,
        limit=limit,
        offset=offset,
    )


@router.post("/consent-records", status_code=201)
def upsert_consent_record(
    payload: ConsentRecordCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CONSENT_WRITE)
    get_contact_or_404(session, auth.workspace_id, payload.contact_id)
    consent_record = session.scalar(
        select(ConsentRecord).where(
            ConsentRecord.workspace_id == auth.workspace_id,
            ConsentRecord.contact_id == payload.contact_id,
            ConsentRecord.channel == payload.channel,
        )
    )

    if consent_record is None:
        consent_record = ConsentRecord(
            workspace_id=auth.workspace_id,
            contact_id=payload.contact_id,
            channel=payload.channel,
            status=payload.status,
            lawful_basis=payload.lawful_basis,
            source=payload.source,
            granted_at=datetime.now(timezone.utc)
            if payload.status == "granted"
            else None,
            revoked_at=datetime.now(timezone.utc)
            if payload.status == "revoked"
            else None,
            extra_data=payload.metadata,
        )
        session.add(consent_record)
        action = "consent_record.created"
    else:
        consent_record.status = payload.status
        consent_record.lawful_basis = payload.lawful_basis
        consent_record.source = payload.source
        consent_record.extra_data = payload.metadata
        consent_record.granted_at = (
            datetime.now(timezone.utc) if payload.status == "granted" else None
        )
        consent_record.revoked_at = (
            datetime.now(timezone.utc) if payload.status == "revoked" else None
        )
        action = "consent_record.updated"

    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action=action,
        actor_id=auth.actor_id,
        resource_type="consent_record",
        resource_id=str(consent_record.id),
        metadata={
            "contact_id": str(payload.contact_id),
            "channel": payload.channel,
            "status": payload.status,
            "role": auth.role,
        },
    )
    session.commit()
    session.refresh(consent_record)
    return _consent_record_dict(consent_record)


@router.get("/content-drafts")
def list_content_drafts(
    organization_id: UUID | None = None,
    status: str | None = Query(default=None, max_length=50),
    channel: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(ContentDraft)
        .where(ContentDraft.workspace_id == auth.workspace_id)
        .order_by(ContentDraft.created_at.desc())
    )
    if organization_id:
        statement = statement.where(ContentDraft.organization_id == organization_id)
    if status:
        statement = statement.where(ContentDraft.status == status)
    if channel:
        statement = statement.where(ContentDraft.channel == channel)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_content_draft_dict,
        limit=limit,
        offset=offset,
    )


@router.post("/content-drafts", status_code=201)
def create_content_draft(
    payload: ContentDraftCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CONTENT_CREATE)
    organization = get_organization_or_404(
        session,
        auth.workspace_id,
        payload.organization_id,
    )
    mock_draft = generate_mock_content_draft(
        organization_name=organization.name,
        channel=payload.channel,
        prompt_text=payload.prompt_text,
    )
    draft_text = payload.draft_text or mock_draft.draft_text
    policy_result = evaluate_content_policy(
        title=payload.title,
        channel=payload.channel,
        prompt_text=payload.prompt_text,
        draft_text=draft_text,
    ).to_dict()
    content_draft = ContentDraft(
        workspace_id=auth.workspace_id,
        organization_id=payload.organization_id,
        title=payload.title,
        channel=payload.channel,
        status="pending_review",
        prompt_version=mock_draft.prompt_version,
        prompt_text=payload.prompt_text,
        draft_text=draft_text,
        model_name=mock_draft.model_name,
        created_by_actor=auth.actor_id,
        model_metadata={
            **mock_draft.model_metadata,
            "policy": policy_result,
            "workflow": {"status": "pending_review"},
        },
        extra_data=payload.metadata,
    )
    session.add(content_draft)
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.created",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "organization_id": str(payload.organization_id),
            "model_name": content_draft.model_name,
            "prompt_version": content_draft.prompt_version,
            "status": content_draft.status,
            "policy_status": policy_result["status"],
            "role": auth.role,
        },
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.policy_evaluated",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "policy_status": policy_result["status"],
            "policy_version": policy_result["version"],
        },
    )
    session.commit()
    session.refresh(content_draft)
    return _content_draft_dict(content_draft)


@router.patch("/content-drafts/{content_draft_id}")
def update_content_draft(
    content_draft_id: UUID,
    payload: ContentDraftUpdate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CONTENT_WRITE)
    content_draft = get_content_draft_or_404(
        session,
        auth.workspace_id,
        content_draft_id,
    )
    updates = payload.model_dump(exclude_unset=True)
    changes: dict[str, Any] = {}

    for field, value in updates.items():
        attribute = "extra_data" if field == "metadata" else field
        previous_value = getattr(content_draft, attribute)
        if previous_value != value:
            setattr(content_draft, attribute, value)
            changes[field] = {"before": previous_value, "after": value}

    policy_result = evaluate_content_policy(
        title=content_draft.title,
        channel=content_draft.channel,
        prompt_text=content_draft.prompt_text,
        draft_text=content_draft.draft_text,
    ).to_dict()
    previous_status = content_draft.status
    content_draft.status = "pending_review"
    content_draft.model_metadata = {
        **content_draft.model_metadata,
        "policy": policy_result,
        "workflow": {
            "status": "pending_review",
            "previous_status": previous_status,
        },
    }

    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.updated",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "changes": changes,
            "previous_status": previous_status,
            "next_status": content_draft.status,
            "role": auth.role,
        },
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.policy_evaluated",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "policy_status": policy_result["status"],
            "policy_version": policy_result["version"],
            "reason": "content_draft.updated",
        },
    )
    session.commit()
    session.refresh(content_draft)
    return _content_draft_dict(content_draft)


@router.delete("/content-drafts/{content_draft_id}")
def delete_content_draft(
    content_draft_id: UUID,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CONTENT_WRITE)
    content_draft = get_content_draft_or_404(
        session,
        auth.workspace_id,
        content_draft_id,
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.deleted",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "title": content_draft.title,
            "status": content_draft.status,
            "organization_id": str(content_draft.organization_id),
            "role": auth.role,
        },
    )
    session.delete(content_draft)
    session.commit()
    return {"status": "deleted", "id": str(content_draft_id)}


@router.get("/review-queue")
def list_review_queue(
    status: str = Query(default="pending_review", max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CONTENT_REVIEW_QUEUE_READ)
    statement = (
        select(ContentDraft)
        .where(
            ContentDraft.workspace_id == auth.workspace_id,
            ContentDraft.status == status,
        )
        .order_by(ContentDraft.created_at.desc())
    )
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_content_draft_dict,
        limit=limit,
        offset=offset,
    )


@router.get("/approval-records")
def list_approval_records(
    content_draft_id: UUID | None = None,
    decision: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(ApprovalRecord)
        .where(ApprovalRecord.workspace_id == auth.workspace_id)
        .order_by(ApprovalRecord.created_at.desc())
    )
    if content_draft_id:
        statement = statement.where(ApprovalRecord.content_draft_id == content_draft_id)
    if decision:
        statement = statement.where(ApprovalRecord.decision == decision)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_approval_record_dict,
        limit=limit,
        offset=offset,
    )


@router.get("/approval-snapshots")
def list_approval_snapshots(
    content_draft_id: UUID | None = None,
    approval_record_id: UUID | None = None,
    decision: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(ApprovalSnapshot)
        .where(ApprovalSnapshot.workspace_id == auth.workspace_id)
        .order_by(ApprovalSnapshot.created_at.desc())
    )
    if content_draft_id:
        statement = statement.where(
            ApprovalSnapshot.content_draft_id == content_draft_id
        )
    if approval_record_id:
        statement = statement.where(
            ApprovalSnapshot.approval_record_id == approval_record_id
        )
    if decision:
        statement = statement.where(ApprovalSnapshot.decision == decision)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_approval_snapshot_dict,
        limit=limit,
        offset=offset,
    )


@router.post("/content-drafts/{content_draft_id}/approve", status_code=201)
def approve_content_draft(
    content_draft_id: UUID,
    payload: ApprovalDecisionCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CONTENT_REVIEW)
    content_draft = get_content_draft_or_404(
        session,
        auth.workspace_id,
        content_draft_id,
    )
    ensure_reviewable_status(content_draft)
    reviewed_status = content_draft.status
    policy = ensure_policy_allows_approval(content_draft)
    content_draft.status = "approved"
    approval_record = ApprovalRecord(
        workspace_id=auth.workspace_id,
        content_draft_id=content_draft.id,
        decision="approved",
        reviewer_actor=auth.actor_id,
        comment=payload.comment,
        decided_at=datetime.now(timezone.utc),
        extra_data={
            **payload.metadata,
            "policy_status": policy.get("status"),
            "policy_version": policy.get("version"),
        },
    )
    session.add(approval_record)
    session.flush()
    approval_snapshot = create_approval_snapshot(
        session,
        content_draft=content_draft,
        approval_record=approval_record,
        policy=policy,
        auth=auth,
        reviewed_status=reviewed_status,
    )
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.approved",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={"approval_record_id": str(approval_record.id), "role": auth.role},
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="approval_snapshot.created",
        actor_id=auth.actor_id,
        resource_type="approval_snapshot",
        resource_id=str(approval_snapshot.id),
        metadata={
            "approval_record_id": str(approval_record.id),
            "content_draft_id": str(content_draft.id),
            "decision": approval_record.decision,
        },
    )
    session.commit()
    session.refresh(approval_record)
    return _approval_record_dict(approval_record)


@router.post("/content-drafts/{content_draft_id}/reject", status_code=201)
def reject_content_draft(
    content_draft_id: UUID,
    payload: ApprovalDecisionCreate,
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, CONTENT_REVIEW)
    content_draft = get_content_draft_or_404(
        session,
        auth.workspace_id,
        content_draft_id,
    )
    ensure_reviewable_status(content_draft)
    reviewed_status = content_draft.status
    policy = policy_result_from_draft(content_draft)
    content_draft.status = "rejected"
    approval_record = ApprovalRecord(
        workspace_id=auth.workspace_id,
        content_draft_id=content_draft.id,
        decision="rejected",
        reviewer_actor=auth.actor_id,
        comment=payload.comment,
        decided_at=datetime.now(timezone.utc),
        extra_data=payload.metadata,
    )
    session.add(approval_record)
    session.flush()
    approval_snapshot = create_approval_snapshot(
        session,
        content_draft=content_draft,
        approval_record=approval_record,
        policy=policy,
        auth=auth,
        reviewed_status=reviewed_status,
    )
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.rejected",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={"approval_record_id": str(approval_record.id), "role": auth.role},
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="approval_snapshot.created",
        actor_id=auth.actor_id,
        resource_type="approval_snapshot",
        resource_id=str(approval_snapshot.id),
        metadata={
            "approval_record_id": str(approval_record.id),
            "content_draft_id": str(content_draft.id),
            "decision": approval_record.decision,
        },
    )
    session.commit()
    session.refresh(approval_record)
    return _approval_record_dict(approval_record)


@router.get("/audit-events")
def list_audit_events(
    action: str | None = Query(default=None, max_length=160),
    resource_type: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, WORKSPACE_READ)
    statement = (
        select(AuditEvent)
        .where(AuditEvent.workspace_id == auth.workspace_id)
        .order_by(AuditEvent.created_at.desc())
    )
    if action:
        statement = statement.where(AuditEvent.action == action)
    if resource_type:
        statement = statement.where(AuditEvent.resource_type == resource_type)
    return _paginated_list(
        session=session,
        statement=statement,
        serializer=_audit_event_dict,
        limit=limit,
        offset=offset,
    )


@router.post("/demo/reset")
def reset_demo_data(
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(auth, DEMO_RESET)
    delete_workspace_records(session, auth.workspace_id)
    session.flush()

    organization = Organization(
        workspace_id=auth.workspace_id,
        name="Acme Wellness Clinic",
        legal_name="Acme Wellness Clinic Ltd.",
        domain="acme-wellness.example",
        industry="Healthcare services",
        status="active",
        extra_data={"demo": True, "segment": "local-services"},
    )
    session.add(organization)
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="organization.created",
        actor_id=auth.actor_id,
        resource_type="organization",
        resource_id=str(organization.id),
        metadata={"seed": True, "role": auth.role},
    )

    contact = Contact(
        workspace_id=auth.workspace_id,
        organization_id=organization.id,
        name="Mia Chen",
        email="mia.chen@example.com",
        phone="+886-900-000-001",
        role="Marketing Manager",
        source="authorized-demo-import",
        extra_data={"demo": True},
    )
    session.add(contact)
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="contact.created",
        actor_id=auth.actor_id,
        resource_type="contact",
        resource_id=str(contact.id),
        metadata={
            "seed": True,
            "organization_id": str(organization.id),
            "role": auth.role,
        },
    )

    consent_record = ConsentRecord(
        workspace_id=auth.workspace_id,
        contact_id=contact.id,
        channel="email",
        status="granted",
        lawful_basis="consent",
        source="demo opt-in form",
        granted_at=datetime.now(timezone.utc),
        extra_data={"demo": True},
    )
    session.add(consent_record)
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="consent_record.created",
        actor_id=auth.actor_id,
        resource_type="consent_record",
        resource_id=str(consent_record.id),
        metadata={"seed": True, "contact_id": str(contact.id), "role": auth.role},
    )

    mock_draft = generate_mock_content_draft(
        organization_name=organization.name,
        channel="email",
        prompt_text="Create a compliant follow-up draft for opted-in customers.",
    )
    seed_policy_result = evaluate_content_policy(
        title="Opt-in review invitation follow-up",
        channel="email",
        prompt_text="Create a compliant follow-up draft for opted-in customers.",
        draft_text=mock_draft.draft_text,
    ).to_dict()
    content_draft = ContentDraft(
        workspace_id=auth.workspace_id,
        organization_id=organization.id,
        title="Opt-in review invitation follow-up",
        channel="email",
        status="pending_review",
        prompt_version=mock_draft.prompt_version,
        prompt_text="Create a compliant follow-up draft for opted-in customers.",
        draft_text=mock_draft.draft_text,
        model_name=mock_draft.model_name,
        created_by_actor=auth.actor_id,
        model_metadata={
            **mock_draft.model_metadata,
            "policy": seed_policy_result,
            "workflow": {"status": "pending_review"},
        },
        extra_data={"demo": True},
    )
    session.add(content_draft)
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.created",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "seed": True,
            "model_name": mock_draft.model_name,
            "status": content_draft.status,
            "policy_status": seed_policy_result["status"],
            "role": auth.role,
        },
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.policy_evaluated",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "seed": True,
            "policy_status": seed_policy_result["status"],
            "policy_version": seed_policy_result["version"],
        },
    )

    approval_record = ApprovalRecord(
        workspace_id=auth.workspace_id,
        content_draft_id=content_draft.id,
        decision="approved",
        reviewer_actor=auth.actor_id,
        comment="Approved for demonstration as a human-reviewed draft.",
        decided_at=datetime.now(timezone.utc),
        extra_data={"demo": True},
    )
    content_draft.status = "approved"
    session.add(approval_record)
    session.flush()
    approval_snapshot = create_approval_snapshot(
        session,
        content_draft=content_draft,
        approval_record=approval_record,
        policy=seed_policy_result,
        auth=auth,
        reviewed_status="pending_review",
    )
    session.flush()
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="content_draft.approved",
        actor_id=auth.actor_id,
        resource_type="content_draft",
        resource_id=str(content_draft.id),
        metadata={
            "seed": True,
            "approval_record_id": str(approval_record.id),
            "role": auth.role,
        },
    )
    record_audit_event(
        session,
        workspace_id=auth.workspace_id,
        action="approval_snapshot.created",
        actor_id=auth.actor_id,
        resource_type="approval_snapshot",
        resource_id=str(approval_snapshot.id),
        metadata={
            "seed": True,
            "approval_record_id": str(approval_record.id),
            "content_draft_id": str(content_draft.id),
            "decision": approval_record.decision,
        },
    )

    session.commit()

    return {
        "status": "ok",
        "message": "Demo data reset and seeded",
        "auth_context": _auth_context_dict(auth),
        "metrics": calculate_workspace_metrics(session, auth.workspace_id),
        "organization": _organization_dict(organization),
        "contact": _contact_dict(contact),
        "consent_record": _consent_record_dict(consent_record),
        "content_draft": _content_draft_dict(content_draft),
        "approval_record": _approval_record_dict(approval_record),
        "approval_snapshot": _approval_snapshot_dict(approval_snapshot),
    }
