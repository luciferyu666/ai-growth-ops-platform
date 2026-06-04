"""Add notification provider and retry scheduling fields.

Revision ID: 20260604_0005
Revises: 20260604_0004
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0005"
down_revision: str | None = "20260604_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notification_outbox",
        sa.Column(
            "provider_name",
            sa.String(length=120),
            nullable=False,
            server_default="mock",
        ),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_notification_outbox_provider_name",
        "notification_outbox",
        ["provider_name"],
    )

    op.add_column(
        "background_jobs",
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_background_jobs_next_run_at",
        "background_jobs",
        ["next_run_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_background_jobs_next_run_at", table_name="background_jobs")
    op.drop_column("background_jobs", "next_run_at")
    op.drop_index(
        "ix_notification_outbox_provider_name",
        table_name="notification_outbox",
    )
    op.drop_column("notification_outbox", "last_attempt_at")
    op.drop_column("notification_outbox", "provider_name")
