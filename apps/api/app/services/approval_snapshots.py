from copy import deepcopy

from sqlalchemy.orm import Session

from app.models import ApprovalRecord, ApprovalSnapshot, ContentDraft
from app.services.auth import AuthContext


SNAPSHOT_VERSION = "approval-snapshot-v1"


def create_approval_snapshot(
    session: Session,
    *,
    content_draft: ContentDraft,
    approval_record: ApprovalRecord,
    policy: dict,
    auth: AuthContext,
    reviewed_status: str,
) -> ApprovalSnapshot:
    snapshot = ApprovalSnapshot(
        workspace_id=approval_record.workspace_id,
        approval_record_id=approval_record.id,
        content_draft_id=content_draft.id,
        decision=approval_record.decision,
        reviewer_actor=approval_record.reviewer_actor,
        snapshot_version=SNAPSHOT_VERSION,
        snapshot_data={
            "content_draft": {
                "id": str(content_draft.id),
                "organization_id": str(content_draft.organization_id),
                "title": content_draft.title,
                "channel": content_draft.channel,
                "status_at_review": reviewed_status,
                "prompt_version": content_draft.prompt_version,
                "prompt_text": content_draft.prompt_text,
                "draft_text": content_draft.draft_text,
                "model_name": content_draft.model_name,
                "model_metadata": deepcopy(content_draft.model_metadata),
                "metadata": deepcopy(content_draft.extra_data),
                "created_by_actor": content_draft.created_by_actor,
            },
            "policy": deepcopy(policy),
            "approval": {
                "id": str(approval_record.id),
                "decision": approval_record.decision,
                "reviewer_actor": approval_record.reviewer_actor,
                "comment": approval_record.comment,
                "decided_at": (
                    approval_record.decided_at.isoformat()
                    if approval_record.decided_at
                    else None
                ),
                "metadata": deepcopy(approval_record.extra_data),
            },
            "reviewer_context": {
                "actor_id": auth.actor_id,
                "role": auth.role,
                "auth_mode": auth.auth_mode,
            },
        },
    )
    session.add(snapshot)
    return snapshot
