from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "external_subject",
            name="uq_users_external_subject",
        ),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    external_subject: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"
    __table_args__ = (UniqueConstraint("slug", name="uq_workspaces_slug"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list["WorkspaceInvitation"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    organizations: Mapped[list["Organization"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    consent_records: Mapped[list["ConsentRecord"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    content_drafts: Mapped[list["ContentDraft"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    approval_records: Mapped[list["ApprovalRecord"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    approval_snapshots: Mapped[list["ApprovalSnapshot"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    notification_outbox: Mapped[list["NotificationOutbox"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    background_jobs: Mapped[list["BackgroundJob"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    operational_events: Mapped[list["OperationalEvent"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class WorkspaceMembership(TimestampMixin, Base):
    __tablename__ = "workspace_memberships"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_memberships_workspace_user",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(80), default="owner", index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class WorkspaceInvitation(TimestampMixin, Base):
    __tablename__ = "workspace_invitations"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_workspace_invitations_token_hash"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(80), default="viewer", index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    invited_by_actor: Mapped[str | None] = mapped_column(String(255))
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="invitations")
    accepted_by_user: Mapped[User | None] = relationship()


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255))
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    industry: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="organizations")
    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    content_drafts: Mapped[list["ContentDraft"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(80))
    role: Mapped[str | None] = mapped_column(String(120))
    source: Mapped[str | None] = mapped_column(String(120))
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="contacts")
    organization: Mapped[Organization] = relationship(back_populates="contacts")
    consent_records: Mapped[list["ConsentRecord"]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
    )


class ConsentRecord(TimestampMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        UniqueConstraint(
            "contact_id",
            "channel",
            name="uq_consent_records_contact_channel",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    contact_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    lawful_basis: Mapped[str | None] = mapped_column(String(120))
    source: Mapped[str | None] = mapped_column(String(255))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="consent_records")
    contact: Mapped[Contact] = relationship(back_populates="consent_records")


class ContentDraft(TimestampMixin, Base):
    __tablename__ = "content_drafts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(120))
    prompt_text: Mapped[str | None] = mapped_column(Text)
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(120))
    created_by_actor: Mapped[str | None] = mapped_column(String(255))
    model_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="content_drafts")
    organization: Mapped[Organization] = relationship(back_populates="content_drafts")
    approval_records: Mapped[list["ApprovalRecord"]] = relationship(
        back_populates="content_draft",
        cascade="all, delete-orphan",
    )


class ApprovalRecord(TimestampMixin, Base):
    __tablename__ = "approval_records"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content_draft_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("content_drafts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    reviewer_actor: Mapped[str | None] = mapped_column(String(255))
    comment: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="approval_records")
    content_draft: Mapped[ContentDraft] = relationship(
        back_populates="approval_records"
    )
    snapshot: Mapped["ApprovalSnapshot | None"] = relationship(
        back_populates="approval_record",
    )


class ApprovalSnapshot(Base):
    __tablename__ = "approval_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "approval_record_id",
            name="uq_approval_snapshots_approval_record_id",
        ),
        Index("ix_approval_snapshots_content_draft", "content_draft_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    approval_record_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("approval_records.id", ondelete="SET NULL"),
        index=True,
    )
    content_draft_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    decision: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    reviewer_actor: Mapped[str | None] = mapped_column(String(255), index=True)
    snapshot_version: Mapped[str] = mapped_column(
        String(80),
        default="approval-snapshot-v1",
        nullable=False,
    )
    snapshot_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="approval_snapshots")
    approval_record: Mapped[ApprovalRecord | None] = relationship(
        back_populates="snapshot",
    )


class NotificationOutbox(TimestampMixin, Base):
    __tablename__ = "notification_outbox"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "idempotency_key",
            name="uq_notification_outbox_workspace_idempotency_key",
        ),
        Index("ix_notification_outbox_workspace_status", "workspace_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    provider_name: Mapped[str] = mapped_column(
        String(120),
        default="mock",
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), index=True)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="notification_outbox")


class BackgroundJob(TimestampMixin, Base):
    __tablename__ = "background_jobs"
    __table_args__ = (
        Index("ix_background_jobs_workspace_status", "workspace_id", "status"),
        Index("ix_background_jobs_resource", "resource_type", "resource_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    queue_name: Mapped[str] = mapped_column(String(120), default="default", index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    resource_type: Mapped[str | None] = mapped_column(String(120))
    resource_id: Mapped[str | None] = mapped_column(String(120))
    created_by_actor: Mapped[str | None] = mapped_column(String(255), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="background_jobs")


class OperationalEvent(Base):
    __tablename__ = "operational_events"
    __table_args__ = (
        Index("ix_operational_events_workspace_created", "workspace_id", "created_at"),
        Index("ix_operational_events_resource", "resource_type", "resource_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(50), default="info", index=True)
    component: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(120), index=True)
    resource_type: Mapped[str | None] = mapped_column(String(120))
    resource_id: Mapped[str | None] = mapped_column(String(120))
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="operational_events")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_resource", "resource_type", "resource_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(255), index=True)
    actor_type: Mapped[str | None] = mapped_column(String(80))
    resource_type: Mapped[str | None] = mapped_column(String(120))
    resource_id: Mapped[str | None] = mapped_column(String(120))
    source: Mapped[str | None] = mapped_column(String(120))
    request_id: Mapped[str | None] = mapped_column(String(120))
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship(back_populates="audit_events")
