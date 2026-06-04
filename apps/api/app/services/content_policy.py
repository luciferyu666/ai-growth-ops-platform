from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.models import ContentDraft

POLICY_VERSION = "content-policy-v1"
BLOCKED_PHRASES = {
    "create fake review": "Fabricated review language is not allowed.",
    "post fake review": "Fabricated review language is not allowed.",
    "generate fake review": "Fabricated review language is not allowed.",
    "fabricate review": "Fabricated review language is not allowed.",
    "buy reviews": "Paid or purchased review language is not allowed.",
    "captcha bypass": "Bypass or evasion instructions are not allowed.",
    "otp bypass": "Bypass or evasion instructions are not allowed.",
    "liveness bypass": "Bypass or evasion instructions are not allowed.",
    "account farm": "Account farming is not allowed.",
    "scrape private": "Unauthorized private data collection is not allowed.",
    "scrape personal data": "Unauthorized private data collection is not allowed.",
    "residential proxy": "Platform evasion infrastructure is not allowed.",
}


@dataclass(frozen=True)
class PolicyResult:
    status: str
    summary: str
    violations: list[str]
    warnings: list[str]
    version: str = POLICY_VERSION
    requires_human_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "violations": self.violations,
            "warnings": self.warnings,
            "version": self.version,
            "requires_human_review": self.requires_human_review,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def evaluate_content_policy(
    *,
    title: str,
    channel: str,
    prompt_text: str | None,
    draft_text: str,
) -> PolicyResult:
    text = " ".join(
        value for value in (title, channel, prompt_text or "", draft_text) if value
    ).lower()
    violations = [
        message
        for phrase, message in BLOCKED_PHRASES.items()
        if phrase in text
    ]

    if violations:
        return PolicyResult(
            status="blocked",
            summary="Policy review blocked approval until the draft is revised.",
            violations=sorted(set(violations)),
            warnings=[],
        )

    warnings = []
    if "review" in text:
        warnings.append("Review-related copy must remain invitation-based and truthful.")

    return PolicyResult(
        status="passed",
        summary="Policy review passed; human approval is still required.",
        violations=[],
        warnings=warnings,
    )


def policy_result_from_draft(content_draft: ContentDraft) -> dict[str, Any]:
    policy = content_draft.model_metadata.get("policy")
    if isinstance(policy, dict):
        return policy

    result = evaluate_content_policy(
        title=content_draft.title,
        channel=content_draft.channel,
        prompt_text=content_draft.prompt_text,
        draft_text=content_draft.draft_text,
    )
    return result.to_dict()


def ensure_policy_allows_approval(content_draft: ContentDraft) -> dict[str, Any]:
    policy = policy_result_from_draft(content_draft)
    if policy.get("status") != "passed":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Content draft cannot be approved until policy passes",
                "policy": policy,
            },
        )
    return policy


def ensure_reviewable_status(content_draft: ContentDraft) -> None:
    if content_draft.status != "pending_review":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Content draft is not pending review",
                "status": content_draft.status,
            },
        )
