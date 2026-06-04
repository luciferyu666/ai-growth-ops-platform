from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditEvent


def record_audit_event(
    session: Session,
    *,
    workspace_id: UUID,
    action: str,
    actor_id: str | None = "demo-operator",
    actor_type: str | None = "operator",
    resource_type: str | None = None,
    resource_id: str | None = None,
    source: str | None = "api",
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        workspace_id=workspace_id,
        action=action,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type=resource_type,
        resource_id=resource_id,
        source=source,
        request_id=request_id,
        extra_data=metadata or {},
    )
    session.add(event)
    return event
