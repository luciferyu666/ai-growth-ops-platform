from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WorkspaceInvitation, WorkspaceMembership
from app.services.auth import IdentityContext, get_or_create_identity_user
from app.services.rbac import ROLE_PERMISSIONS


@dataclass(frozen=True)
class InvitationAcceptance:
    invitation: WorkspaceInvitation
    membership: WorkspaceMembership
    membership_created: bool


def normalize_invitation_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid invitation email")
    return email


def validate_invitation_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="Invalid workspace role")
    return normalized


def generate_invitation_token() -> str:
    return token_urlsafe(32)


def invitation_token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_workspace_invitation(
    session: Session,
    *,
    workspace_id: UUID,
    email: str,
    role: str,
    invited_by_actor: str,
    expires_in_days: int,
    metadata: dict,
) -> tuple[WorkspaceInvitation, str]:
    token = generate_invitation_token()
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        email=normalize_invitation_email(email),
        role=validate_invitation_role(role),
        status="pending",
        token_hash=invitation_token_hash(token),
        invited_by_actor=invited_by_actor,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        extra_data=metadata,
    )
    session.add(invitation)
    return invitation, token


def accept_workspace_invitation(
    session: Session,
    *,
    token: str,
    identity: IdentityContext,
) -> InvitationAcceptance:
    token = token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Invitation token is required")

    invitation = session.scalar(
        select(WorkspaceInvitation).where(
            WorkspaceInvitation.token_hash == invitation_token_hash(token)
        )
    )
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="Invitation is not pending")
    if invitation.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="Invitation has expired")
    if invitation.email != identity.user_email:
        raise HTTPException(status_code=403, detail="Invitation email mismatch")

    user, _ = get_or_create_identity_user(session, identity)
    session.flush()

    membership_created = False
    membership = session.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == invitation.workspace_id,
            WorkspaceMembership.user_id == user.id,
        )
    )
    if membership is None:
        membership = WorkspaceMembership(
            workspace_id=invitation.workspace_id,
            user_id=user.id,
            role=invitation.role,
            status="active",
            extra_data={"invitation_id": str(invitation.id)},
        )
        session.add(membership)
        membership_created = True
    else:
        membership.role = invitation.role
        membership.status = "active"
        membership.extra_data = {
            **membership.extra_data,
            "invitation_id": str(invitation.id),
        }

    invitation.status = "accepted"
    invitation.accepted_by_user_id = user.id
    invitation.accepted_at = datetime.now(timezone.utc)
    return InvitationAcceptance(
        invitation=invitation,
        membership=membership,
        membership_created=membership_created,
    )
