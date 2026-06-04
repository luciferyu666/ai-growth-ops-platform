"""Add notification outbox, background jobs, and operational events.

Revision ID: 20260604_0004
Revises: 20260604_0003
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260604_0004"
down_revision: str | None = "20260604_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _metadata_column() -> sa.Column:
    return sa.Column(
        "metadata",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "notification_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default="3",
        ),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        _metadata_column(),
        *_timestamp_columns(),
        sa.UniqueConstraint(
            "workspace_id",
            "idempotency_key",
            name="uq_notification_outbox_workspace_idempotency_key",
        ),
    )
    op.create_index(
        "ix_notification_outbox_workspace_id",
        "notification_outbox",
        ["workspace_id"],
    )
    op.create_index("ix_notification_outbox_channel", "notification_outbox", ["channel"])
    op.create_index(
        "ix_notification_outbox_recipient",
        "notification_outbox",
        ["recipient"],
    )
    op.create_index("ix_notification_outbox_status", "notification_outbox", ["status"])
    op.create_index(
        "ix_notification_outbox_next_attempt_at",
        "notification_outbox",
        ["next_attempt_at"],
    )
    op.create_index(
        "ix_notification_outbox_idempotency_key",
        "notification_outbox",
        ["idempotency_key"],
    )
    op.create_index(
        "ix_notification_outbox_workspace_status",
        "notification_outbox",
        ["workspace_id", "status"],
    )

    op.create_table(
        "background_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(length=120), nullable=False),
        sa.Column(
            "queue_name",
            sa.String(length=120),
            nullable=False,
            server_default="default",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("resource_type", sa.String(length=120), nullable=True),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("created_by_actor", sa.String(length=255), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        _metadata_column(),
        *_timestamp_columns(),
    )
    op.create_index("ix_background_jobs_workspace_id", "background_jobs", ["workspace_id"])
    op.create_index("ix_background_jobs_job_type", "background_jobs", ["job_type"])
    op.create_index("ix_background_jobs_queue_name", "background_jobs", ["queue_name"])
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"])
    op.create_index(
        "ix_background_jobs_celery_task_id",
        "background_jobs",
        ["celery_task_id"],
    )
    op.create_index(
        "ix_background_jobs_created_by_actor",
        "background_jobs",
        ["created_by_actor"],
    )
    op.create_index(
        "ix_background_jobs_workspace_status",
        "background_jobs",
        ["workspace_id", "status"],
    )
    op.create_index(
        "ix_background_jobs_resource",
        "background_jobs",
        ["resource_type", "resource_id"],
    )

    op.create_table(
        "operational_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=50),
            nullable=False,
            server_default="info",
        ),
        sa.Column("component", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="open",
        ),
        sa.Column("correlation_id", sa.String(length=120), nullable=True),
        sa.Column("resource_type", sa.String(length=120), nullable=True),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        _metadata_column(),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_operational_events_workspace_id",
        "operational_events",
        ["workspace_id"],
    )
    op.create_index(
        "ix_operational_events_severity",
        "operational_events",
        ["severity"],
    )
    op.create_index(
        "ix_operational_events_component",
        "operational_events",
        ["component"],
    )
    op.create_index(
        "ix_operational_events_event_type",
        "operational_events",
        ["event_type"],
    )
    op.create_index("ix_operational_events_status", "operational_events", ["status"])
    op.create_index(
        "ix_operational_events_correlation_id",
        "operational_events",
        ["correlation_id"],
    )
    op.create_index(
        "ix_operational_events_created_at",
        "operational_events",
        ["created_at"],
    )
    op.create_index(
        "ix_operational_events_workspace_created",
        "operational_events",
        ["workspace_id", "created_at"],
    )
    op.create_index(
        "ix_operational_events_resource",
        "operational_events",
        ["resource_type", "resource_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_operational_events_resource", table_name="operational_events")
    op.drop_index(
        "ix_operational_events_workspace_created",
        table_name="operational_events",
    )
    op.drop_index("ix_operational_events_created_at", table_name="operational_events")
    op.drop_index("ix_operational_events_correlation_id", table_name="operational_events")
    op.drop_index("ix_operational_events_status", table_name="operational_events")
    op.drop_index("ix_operational_events_event_type", table_name="operational_events")
    op.drop_index("ix_operational_events_component", table_name="operational_events")
    op.drop_index("ix_operational_events_severity", table_name="operational_events")
    op.drop_index("ix_operational_events_workspace_id", table_name="operational_events")
    op.drop_table("operational_events")

    op.drop_index("ix_background_jobs_resource", table_name="background_jobs")
    op.drop_index("ix_background_jobs_workspace_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_created_by_actor", table_name="background_jobs")
    op.drop_index("ix_background_jobs_celery_task_id", table_name="background_jobs")
    op.drop_index("ix_background_jobs_status", table_name="background_jobs")
    op.drop_index("ix_background_jobs_queue_name", table_name="background_jobs")
    op.drop_index("ix_background_jobs_job_type", table_name="background_jobs")
    op.drop_index("ix_background_jobs_workspace_id", table_name="background_jobs")
    op.drop_table("background_jobs")

    op.drop_index(
        "ix_notification_outbox_workspace_status",
        table_name="notification_outbox",
    )
    op.drop_index(
        "ix_notification_outbox_idempotency_key",
        table_name="notification_outbox",
    )
    op.drop_index(
        "ix_notification_outbox_next_attempt_at",
        table_name="notification_outbox",
    )
    op.drop_index("ix_notification_outbox_status", table_name="notification_outbox")
    op.drop_index("ix_notification_outbox_recipient", table_name="notification_outbox")
    op.drop_index("ix_notification_outbox_channel", table_name="notification_outbox")
    op.drop_index(
        "ix_notification_outbox_workspace_id",
        table_name="notification_outbox",
    )
    op.drop_table("notification_outbox")
