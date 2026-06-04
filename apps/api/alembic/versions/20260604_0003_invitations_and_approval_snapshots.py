"""Add workspace invitations and immutable approval snapshots.

Revision ID: 20260604_0003
Revises: 20260603_0002
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260604_0003"
down_revision: str | None = "20260603_0002"
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
        "workspace_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "role",
            sa.String(length=80),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("invited_by_actor", sa.String(length=255), nullable=True),
        sa.Column(
            "accepted_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        _metadata_column(),
        *_timestamp_columns(),
        sa.UniqueConstraint(
            "token_hash",
            name="uq_workspace_invitations_token_hash",
        ),
    )
    op.create_index(
        "ix_workspace_invitations_workspace_id",
        "workspace_invitations",
        ["workspace_id"],
    )
    op.create_index("ix_workspace_invitations_email", "workspace_invitations", ["email"])
    op.create_index("ix_workspace_invitations_role", "workspace_invitations", ["role"])
    op.create_index(
        "ix_workspace_invitations_status",
        "workspace_invitations",
        ["status"],
    )
    op.create_index(
        "ix_workspace_invitations_accepted_by_user_id",
        "workspace_invitations",
        ["accepted_by_user_id"],
    )
    op.create_index(
        "ix_workspace_invitations_expires_at",
        "workspace_invitations",
        ["expires_at"],
    )

    op.create_table(
        "approval_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "approval_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("approval_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("content_draft_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("reviewer_actor", sa.String(length=255), nullable=True),
        sa.Column(
            "snapshot_version",
            sa.String(length=80),
            nullable=False,
            server_default="approval-snapshot-v1",
        ),
        sa.Column(
            "snapshot_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "approval_record_id",
            name="uq_approval_snapshots_approval_record_id",
        ),
    )
    op.create_index(
        "ix_approval_snapshots_workspace_id",
        "approval_snapshots",
        ["workspace_id"],
    )
    op.create_index(
        "ix_approval_snapshots_approval_record_id",
        "approval_snapshots",
        ["approval_record_id"],
    )
    op.create_index(
        "ix_approval_snapshots_content_draft",
        "approval_snapshots",
        ["content_draft_id"],
    )
    op.create_index(
        "ix_approval_snapshots_decision",
        "approval_snapshots",
        ["decision"],
    )
    op.create_index(
        "ix_approval_snapshots_reviewer_actor",
        "approval_snapshots",
        ["reviewer_actor"],
    )
    op.create_index(
        "ix_approval_snapshots_created_at",
        "approval_snapshots",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_approval_snapshots_created_at", table_name="approval_snapshots")
    op.drop_index("ix_approval_snapshots_reviewer_actor", table_name="approval_snapshots")
    op.drop_index("ix_approval_snapshots_decision", table_name="approval_snapshots")
    op.drop_index(
        "ix_approval_snapshots_content_draft",
        table_name="approval_snapshots",
    )
    op.drop_index(
        "ix_approval_snapshots_approval_record_id",
        table_name="approval_snapshots",
    )
    op.drop_index("ix_approval_snapshots_workspace_id", table_name="approval_snapshots")
    op.drop_table("approval_snapshots")

    op.drop_index(
        "ix_workspace_invitations_expires_at",
        table_name="workspace_invitations",
    )
    op.drop_index(
        "ix_workspace_invitations_accepted_by_user_id",
        table_name="workspace_invitations",
    )
    op.drop_index("ix_workspace_invitations_status", table_name="workspace_invitations")
    op.drop_index("ix_workspace_invitations_role", table_name="workspace_invitations")
    op.drop_index("ix_workspace_invitations_email", table_name="workspace_invitations")
    op.drop_index(
        "ix_workspace_invitations_workspace_id",
        table_name="workspace_invitations",
    )
    op.drop_table("workspace_invitations")
