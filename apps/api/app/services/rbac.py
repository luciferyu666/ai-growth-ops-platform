from fastapi import HTTPException

from app.services.auth import AuthContext

WORKSPACE_READ = "workspace.read"
WORKSPACE_INVITE = "workspace.invite"
OPERATIONS_RUN = "operations.run"
CRM_WRITE = "crm.write"
CONSENT_WRITE = "consent.write"
CONTENT_CREATE = "content.create"
CONTENT_WRITE = "content.write"
CONTENT_REVIEW_QUEUE_READ = "content.review_queue.read"
CONTENT_REVIEW = "content.review"
DEMO_RESET = "demo.reset"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        WORKSPACE_READ,
        WORKSPACE_INVITE,
        OPERATIONS_RUN,
        CRM_WRITE,
        CONSENT_WRITE,
        CONTENT_CREATE,
        CONTENT_WRITE,
        CONTENT_REVIEW_QUEUE_READ,
        CONTENT_REVIEW,
        DEMO_RESET,
    },
    "admin": {
        WORKSPACE_READ,
        WORKSPACE_INVITE,
        OPERATIONS_RUN,
        CRM_WRITE,
        CONSENT_WRITE,
        CONTENT_CREATE,
        CONTENT_WRITE,
        CONTENT_REVIEW_QUEUE_READ,
        CONTENT_REVIEW,
        DEMO_RESET,
    },
    "operator": {
        WORKSPACE_READ,
        OPERATIONS_RUN,
        CRM_WRITE,
        CONSENT_WRITE,
        CONTENT_CREATE,
        CONTENT_WRITE,
        CONTENT_REVIEW_QUEUE_READ,
    },
    "reviewer": {
        WORKSPACE_READ,
        CONTENT_REVIEW_QUEUE_READ,
        CONTENT_REVIEW,
    },
    "viewer": {
        WORKSPACE_READ,
        CONTENT_REVIEW_QUEUE_READ,
    },
}


def permissions_for_role(role: str) -> set[str]:
    return ROLE_PERMISSIONS.get(role, set())


def require_permission(auth: AuthContext, permission: str) -> None:
    if permission not in permissions_for_role(auth.role):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Permission denied",
                "required_permission": permission,
                "role": auth.role,
            },
        )
