from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

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


def workspace_filter(statement: Select, model: type, workspace_id: UUID) -> Select:
    return statement.where(model.workspace_id == workspace_id)


def get_workspace_metrics(session: Session, workspace_id: UUID) -> dict[str, int]:
    return {
        "organizations": session.scalar(
            select(func.count(Organization.id)).where(
                Organization.workspace_id == workspace_id
            )
        )
        or 0,
        "contacts": session.scalar(
            select(func.count(Contact.id)).where(Contact.workspace_id == workspace_id)
        )
        or 0,
        "consent_records": session.scalar(
            select(func.count(ConsentRecord.id)).where(
                ConsentRecord.workspace_id == workspace_id
            )
        )
        or 0,
        "content_drafts": session.scalar(
            select(func.count(ContentDraft.id)).where(
                ContentDraft.workspace_id == workspace_id
            )
        )
        or 0,
        "pending_drafts": session.scalar(
            select(func.count(ContentDraft.id)).where(
                ContentDraft.workspace_id == workspace_id,
                ContentDraft.status == "pending_review",
            )
        )
        or 0,
        "approved_drafts": session.scalar(
            select(func.count(ContentDraft.id)).where(
                ContentDraft.workspace_id == workspace_id,
                ContentDraft.status == "approved",
            )
        )
        or 0,
        "approval_records": session.scalar(
            select(func.count(ApprovalRecord.id)).where(
                ApprovalRecord.workspace_id == workspace_id
            )
        )
        or 0,
        "approval_snapshots": session.scalar(
            select(func.count(ApprovalSnapshot.id)).where(
                ApprovalSnapshot.workspace_id == workspace_id
            )
        )
        or 0,
        "pending_invitations": session.scalar(
            select(func.count(WorkspaceInvitation.id)).where(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.status == "pending",
            )
        )
        or 0,
        "pending_notifications": session.scalar(
            select(func.count(NotificationOutbox.id)).where(
                NotificationOutbox.workspace_id == workspace_id,
                NotificationOutbox.status.in_(("pending", "retry_scheduled")),
            )
        )
        or 0,
        "retry_scheduled_notifications": session.scalar(
            select(func.count(NotificationOutbox.id)).where(
                NotificationOutbox.workspace_id == workspace_id,
                NotificationOutbox.status == "retry_scheduled",
            )
        )
        or 0,
        "delivered_notifications": session.scalar(
            select(func.count(NotificationOutbox.id)).where(
                NotificationOutbox.workspace_id == workspace_id,
                NotificationOutbox.status == "delivered",
            )
        )
        or 0,
        "dead_letter_notifications": session.scalar(
            select(func.count(NotificationOutbox.id)).where(
                NotificationOutbox.workspace_id == workspace_id,
                NotificationOutbox.status == "dead_letter",
            )
        )
        or 0,
        "queued_jobs": session.scalar(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.workspace_id == workspace_id,
                BackgroundJob.status.in_(("queued", "retry_scheduled")),
            )
        )
        or 0,
        "failed_jobs": session.scalar(
            select(func.count(BackgroundJob.id)).where(
                BackgroundJob.workspace_id == workspace_id,
                BackgroundJob.status.in_(("failed", "dead_letter")),
            )
        )
        or 0,
        "open_operation_alerts": session.scalar(
            select(func.count(OperationalEvent.id)).where(
                OperationalEvent.workspace_id == workspace_id,
                OperationalEvent.component == "operations_monitor",
                OperationalEvent.status == "open",
            )
        )
        or 0,
        "operational_events": session.scalar(
            select(func.count(OperationalEvent.id)).where(
                OperationalEvent.workspace_id == workspace_id
            )
        )
        or 0,
        "audit_events": session.scalar(
            select(func.count(AuditEvent.id)).where(
                AuditEvent.workspace_id == workspace_id
            )
        )
        or 0,
    }


def get_organization_or_404(
    session: Session,
    workspace_id: UUID,
    organization_id: UUID,
) -> Organization:
    organization = session.scalar(
        select(Organization).where(
            Organization.id == organization_id,
            Organization.workspace_id == workspace_id,
        )
    )
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


def get_contact_or_404(
    session: Session,
    workspace_id: UUID,
    contact_id: UUID,
) -> Contact:
    contact = session.scalar(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.workspace_id == workspace_id,
        )
    )
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


def get_content_draft_or_404(
    session: Session,
    workspace_id: UUID,
    content_draft_id: UUID,
) -> ContentDraft:
    content_draft = session.scalar(
        select(ContentDraft).where(
            ContentDraft.id == content_draft_id,
            ContentDraft.workspace_id == workspace_id,
        )
    )
    if content_draft is None:
        raise HTTPException(status_code=404, detail="Content draft not found")
    return content_draft


def delete_workspace_records(session: Session, workspace_id: UUID) -> None:
    for model in (
        ApprovalSnapshot,
        ApprovalRecord,
        ContentDraft,
        ConsentRecord,
        Contact,
        Organization,
        WorkspaceInvitation,
        NotificationOutbox,
        BackgroundJob,
        OperationalEvent,
        AuditEvent,
    ):
        records = session.scalars(
            select(model).where(model.workspace_id == workspace_id)
        ).all()
        for record in records:
            session.delete(record)
