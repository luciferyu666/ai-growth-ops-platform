"""Add workspace ownership and demo auth identity tables.

Revision ID: 20260603_0002
Revises: 20260603_0001
Create Date: 2026-06-03
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260603_0002"
down_revision: str | None = "20260603_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEMO_WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
DEMO_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
DEMO_MEMBERSHIP_ID = UUID("33333333-3333-4333-8333-333333333333")


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


def _workspace_id_column() -> sa.Column:
    return sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True)


def _add_workspace_scope(table_name: str) -> None:
    op.add_column(table_name, _workspace_id_column())
    op.execute(
        sa.text(
            f"UPDATE {table_name} SET workspace_id = :workspace_id "
            "WHERE workspace_id IS NULL"
        ).bindparams(workspace_id=DEMO_WORKSPACE_ID)
    )
    op.alter_column(table_name, "workspace_id", nullable=False)
    op.create_foreign_key(
        f"fk_{table_name}_workspace_id_workspaces",
        table_name,
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(f"ix_{table_name}_workspace_id", table_name, ["workspace_id"])


def _drop_workspace_scope(table_name: str) -> None:
    op.drop_index(f"ix_{table_name}_workspace_id", table_name=table_name)
    op.drop_constraint(
        f"fk_{table_name}_workspace_id_workspaces",
        table_name,
        type_="foreignkey",
    )
    op.drop_column(table_name, "workspace_id")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
        _metadata_column(),
        *_timestamp_columns(),
        sa.UniqueConstraint("external_subject", name="uq_users_external_subject"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_external_subject", "users", ["external_subject"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
        _metadata_column(),
        *_timestamp_columns(),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"])
    op.create_index("ix_workspaces_status", "workspaces", ["status"])

    op.create_table(
        "workspace_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=80),
            nullable=False,
            server_default="owner",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
        _metadata_column(),
        *_timestamp_columns(),
        sa.UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_memberships_workspace_user",
        ),
    )
    op.create_index(
        "ix_workspace_memberships_workspace_id",
        "workspace_memberships",
        ["workspace_id"],
    )
    op.create_index(
        "ix_workspace_memberships_user_id",
        "workspace_memberships",
        ["user_id"],
    )
    op.create_index("ix_workspace_memberships_role", "workspace_memberships", ["role"])
    op.create_index(
        "ix_workspace_memberships_status",
        "workspace_memberships",
        ["status"],
    )

    users_table = sa.table(
        "users",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("external_subject", sa.String),
        sa.column("email", sa.String),
        sa.column("display_name", sa.String),
        sa.column("status", sa.String),
        sa.column("metadata", postgresql.JSONB),
    )
    workspaces_table = sa.table(
        "workspaces",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("status", sa.String),
        sa.column("metadata", postgresql.JSONB),
    )
    memberships_table = sa.table(
        "workspace_memberships",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("workspace_id", postgresql.UUID(as_uuid=True)),
        sa.column("user_id", postgresql.UUID(as_uuid=True)),
        sa.column("role", sa.String),
        sa.column("status", sa.String),
        sa.column("metadata", postgresql.JSONB),
    )

    op.bulk_insert(
        users_table,
        [
            {
                "id": DEMO_USER_ID,
                "external_subject": "demo:operator@ai-growth-ops.local",
                "email": "operator@ai-growth-ops.local",
                "display_name": "Demo Operator",
                "status": "active",
                "metadata": {"seed": True, "auth_mode": "demo-header"},
            }
        ],
    )
    op.bulk_insert(
        workspaces_table,
        [
            {
                "id": DEMO_WORKSPACE_ID,
                "slug": "demo-growth-ops",
                "name": "Demo Growth Ops Workspace",
                "status": "active",
                "metadata": {"seed": True},
            }
        ],
    )
    op.bulk_insert(
        memberships_table,
        [
            {
                "id": DEMO_MEMBERSHIP_ID,
                "workspace_id": DEMO_WORKSPACE_ID,
                "user_id": DEMO_USER_ID,
                "role": "owner",
                "status": "active",
                "metadata": {"seed": True},
            }
        ],
    )

    for table_name in (
        "organizations",
        "contacts",
        "consent_records",
        "content_drafts",
        "approval_records",
        "audit_events",
    ):
        _add_workspace_scope(table_name)


def downgrade() -> None:
    for table_name in (
        "audit_events",
        "approval_records",
        "content_drafts",
        "consent_records",
        "contacts",
        "organizations",
    ):
        _drop_workspace_scope(table_name)

    op.drop_index("ix_workspace_memberships_status", table_name="workspace_memberships")
    op.drop_index("ix_workspace_memberships_role", table_name="workspace_memberships")
    op.drop_index(
        "ix_workspace_memberships_user_id",
        table_name="workspace_memberships",
    )
    op.drop_index(
        "ix_workspace_memberships_workspace_id",
        table_name="workspace_memberships",
    )
    op.drop_table("workspace_memberships")

    op.drop_index("ix_workspaces_status", table_name="workspaces")
    op.drop_index("ix_workspaces_slug", table_name="workspaces")
    op.drop_table("workspaces")

    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_external_subject", table_name="users")
    op.drop_table("users")
