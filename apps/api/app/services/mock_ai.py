from dataclasses import dataclass


@dataclass(frozen=True)
class MockDraft:
    draft_text: str
    prompt_version: str
    model_name: str
    model_metadata: dict[str, str]


def generate_mock_content_draft(
    *,
    organization_name: str,
    channel: str,
    prompt_text: str | None,
) -> MockDraft:
    normalized_channel = channel.replace("_", " ").title()
    source_prompt = prompt_text or "Create a concise compliant customer follow-up draft."

    return MockDraft(
        draft_text=(
            f"For {organization_name}, prepare a {normalized_channel} draft that "
            "focuses on verified customer context, clear value, and a human review "
            "step before any outbound use. The message should invite a relevant "
            "conversation without implying fabricated reviews or unauthorized data use."
        ),
        prompt_version="mock-growth-draft-v1",
        model_name="mock-ai-content-service",
        model_metadata={
            "provider": "local-mock",
            "purpose": "proposal-demo",
            "source_prompt": source_prompt,
        },
    )
