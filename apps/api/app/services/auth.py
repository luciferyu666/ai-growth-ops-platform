from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session
from app.models import User, Workspace, WorkspaceMembership

DEFAULT_DEMO_USER_EMAIL = "operator@ai-growth-ops.local"
DEFAULT_DEMO_WORKSPACE_SLUG = "demo-growth-ops"
DEFAULT_DEMO_WORKSPACE_NAME = "Demo Growth Ops Workspace"


@dataclass(frozen=True)
class IdentityContext:
    external_subject: str
    user_email: str
    user_display_name: str | None
    auth_mode: str
    claims: dict[str, Any] = field(default_factory=dict)

    @property
    def actor_id(self) -> str:
        return self.user_email


@dataclass(frozen=True)
class AuthContext:
    user_id: UUID
    user_email: str
    user_display_name: str | None
    workspace_id: UUID
    workspace_slug: str
    workspace_name: str
    membership_id: UUID
    role: str
    auth_mode: str = "demo-header"

    @property
    def actor_id(self) -> str:
        return self.user_email


def _provider(settings: Settings) -> str:
    return settings.auth_provider.strip().lower()


def _normalize_email(value: str | None) -> str:
    email = (value or DEFAULT_DEMO_USER_EMAIL).strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid user email")
    return email


def _normalize_required_email(value: str | None) -> str:
    if not value:
        raise HTTPException(status_code=403, detail="Token is missing email claim")
    return _normalize_email(value)


def _normalize_slug(value: str | None) -> str:
    raw_slug = (value or DEFAULT_DEMO_WORKSPACE_SLUG).strip().lower()
    normalized = "".join(
        character if character.isalnum() else "-" for character in raw_slug
    ).strip("-")
    normalized = "-".join(part for part in normalized.split("-") if part)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid workspace slug")
    return normalized[:120]


def _default_display_name(email: str) -> str:
    return email.split("@", maxsplit=1)[0].replace(".", " ").replace("-", " ").title()


def _demo_identity(request: Request) -> IdentityContext:
    email = _normalize_email(request.headers.get("x-demo-user-email"))
    display_name = (
        request.headers.get("x-demo-user-name") or _default_display_name(email)
    ).strip()
    external_subject = request.headers.get("x-demo-user-subject") or f"demo:{email}"
    return IdentityContext(
        external_subject=external_subject,
        user_email=email,
        user_display_name=display_name,
        auth_mode="demo-header",
        claims={"provider": "demo-header"},
    )


def _auth0_issuer(settings: Settings) -> str:
    issuer = settings.auth0_issuer_base_url or settings.auth0_domain
    if not issuer:
        raise HTTPException(status_code=503, detail="Auth0 issuer is not configured")
    issuer = issuer.strip()
    if not issuer.startswith(("http://", "https://")):
        issuer = f"https://{issuer}"
    return f"{issuer.rstrip('/')}/"


def _bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Bearer token is required")
    return token.strip()


def _namespaced_claim(payload: dict[str, Any], suffix: str) -> Any:
    for key, value in payload.items():
        if key.endswith(f"/{suffix}"):
            return value
    return None


def _auth0_identity(request: Request, settings: Settings) -> IdentityContext:
    if not settings.auth0_audience:
        raise HTTPException(status_code=503, detail="Auth0 audience is not configured")

    issuer = _auth0_issuer(settings)
    token = _bearer_token(request)
    jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"

    try:
        signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=issuer,
        )
    except (InvalidTokenError, PyJWKClientError) as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=401, detail="Invalid bearer token payload")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Token is missing subject claim")

    email = _normalize_required_email(
        payload.get("email") or _namespaced_claim(payload, "email")
    )
    display_name = (
        payload.get("name")
        or payload.get("nickname")
        or _namespaced_claim(payload, "name")
        or _default_display_name(email)
    )
    return IdentityContext(
        external_subject=f"auth0:{subject}",
        user_email=email,
        user_display_name=str(display_name),
        auth_mode="auth0",
        claims=payload,
    )


def _resolve_identity_context(
    request: Request,
    settings: Settings,
) -> IdentityContext:
    provider = _provider(settings)
    if provider in {"demo", "demo-header", "local"}:
        return _demo_identity(request)
    if provider == "auth0":
        return _auth0_identity(request, settings)
    raise HTTPException(
        status_code=500,
        detail=f"Unsupported auth provider: {settings.auth_provider}",
    )


def get_identity_context(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> IdentityContext:
    return _resolve_identity_context(request, settings)


def get_or_create_identity_user(
    session: Session,
    identity: IdentityContext,
) -> tuple[User, bool]:
    changed = False
    user = session.scalar(
        select(User).where(User.external_subject == identity.external_subject)
    )
    if user is None:
        user = session.scalar(select(User).where(User.email == identity.user_email))

    if user is None:
        user = User(
            external_subject=identity.external_subject,
            email=identity.user_email,
            display_name=identity.user_display_name,
            status="active",
            extra_data={"auth_mode": identity.auth_mode},
        )
        session.add(user)
        changed = True
    else:
        if user.external_subject != identity.external_subject:
            user.external_subject = identity.external_subject
            changed = True
        if user.display_name != identity.user_display_name:
            user.display_name = identity.user_display_name
            changed = True
        if user.extra_data.get("auth_mode") != identity.auth_mode:
            user.extra_data = {**user.extra_data, "auth_mode": identity.auth_mode}
            changed = True

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User is inactive")

    return user, changed


def _demo_auth_context(
    request: Request,
    session: Session,
    identity: IdentityContext,
) -> AuthContext:
    workspace_slug = _normalize_slug(request.headers.get("x-demo-workspace-slug"))
    workspace_name = (
        request.headers.get("x-demo-workspace-name")
        or (
            DEFAULT_DEMO_WORKSPACE_NAME
            if workspace_slug == DEFAULT_DEMO_WORKSPACE_SLUG
            else workspace_slug.replace("-", " ").title()
        )
    ).strip()
    role = (request.headers.get("x-demo-role") or "owner").strip().lower()

    user, changed = get_or_create_identity_user(session, identity)
    workspace = session.scalar(
        select(Workspace).where(Workspace.slug == workspace_slug)
    )
    if workspace is None:
        workspace = Workspace(
            slug=workspace_slug,
            name=workspace_name,
            status="active",
            extra_data={"auth_mode": identity.auth_mode},
        )
        session.add(workspace)
        changed = True
    else:
        if workspace.name != workspace_name:
            workspace.name = workspace_name
            changed = True

    session.flush()

    membership = session.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace.id,
            WorkspaceMembership.user_id == user.id,
        )
    )
    if membership is None:
        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role=role,
            status="active",
            extra_data={"auth_mode": identity.auth_mode},
        )
        session.add(membership)
        changed = True
    elif membership.role != role:
        membership.role = role
        changed = True

    if workspace.status != "active":
        raise HTTPException(status_code=403, detail="Workspace is inactive")
    if membership.status != "active":
        raise HTTPException(status_code=403, detail="Membership is inactive")

    if changed:
        session.commit()
        session.refresh(user)
        session.refresh(workspace)
        session.refresh(membership)

    return AuthContext(
        user_id=user.id,
        user_email=user.email,
        user_display_name=user.display_name,
        workspace_id=workspace.id,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        membership_id=membership.id,
        role=membership.role,
        auth_mode=identity.auth_mode,
    )


def _auth0_workspace_slug(request: Request, identity: IdentityContext) -> str:
    workspace_slug = (
        request.headers.get("x-workspace-slug")
        or request.headers.get("x-demo-workspace-slug")
        or identity.claims.get("https://ai-growth-ops.local/workspace_slug")
    )
    if not workspace_slug:
        raise HTTPException(status_code=400, detail="Workspace slug is required")
    return _normalize_slug(str(workspace_slug))


def _membership_auth_context(
    request: Request,
    session: Session,
    identity: IdentityContext,
) -> AuthContext:
    workspace_slug = _auth0_workspace_slug(request, identity)
    user, changed = get_or_create_identity_user(session, identity)
    workspace = session.scalar(
        select(Workspace).where(Workspace.slug == workspace_slug)
    )
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    session.flush()
    membership = session.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace.id,
            WorkspaceMembership.user_id == user.id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Workspace membership required")
    if workspace.status != "active":
        raise HTTPException(status_code=403, detail="Workspace is inactive")
    if membership.status != "active":
        raise HTTPException(status_code=403, detail="Membership is inactive")

    if changed:
        session.commit()
        session.refresh(user)
        session.refresh(workspace)
        session.refresh(membership)

    return AuthContext(
        user_id=user.id,
        user_email=user.email,
        user_display_name=user.display_name,
        workspace_id=workspace.id,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        membership_id=membership.id,
        role=membership.role,
        auth_mode=identity.auth_mode,
    )


def get_auth_context(
    request: Request,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    """Resolve the current identity, workspace, and membership.

    Local demos use replaceable `X-Demo-*` headers. Production Auth0 mode validates
    bearer JWTs and requires an existing workspace membership, usually created via
    the invitation acceptance flow.
    """

    identity = _resolve_identity_context(request, settings)
    if identity.auth_mode == "demo-header":
        return _demo_auth_context(request, session, identity)
    return _membership_auth_context(request, session, identity)
