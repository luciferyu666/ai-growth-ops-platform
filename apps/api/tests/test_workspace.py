from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def _headers(
    workspace_slug: str,
    user_email: str = "operator@example.test",
    role: str = "owner",
) -> dict:
    return {
        "x-demo-workspace-slug": workspace_slug,
        "x-demo-user-email": user_email,
        "x-demo-user-name": "Test Operator",
        "x-demo-role": role,
    }


def _items(response) -> list[dict]:
    payload = response.json()
    return payload["items"]


def _pagination(response) -> dict:
    payload = response.json()
    return payload["pagination"]


def test_demo_reset_seeds_complete_vertical_slice() -> None:
    client = TestClient(app)
    headers = _headers("mvp002-reset")

    response = client.post("/workspace/demo/reset", headers=headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["auth_context"]["workspace"]["slug"] == "mvp002-reset"
    assert payload["auth_context"]["actor_id"] == "operator@example.test"
    assert payload["metrics"]["organizations"] == 1
    assert payload["metrics"]["contacts"] == 1
    assert payload["metrics"]["consent_records"] == 1
    assert payload["metrics"]["content_drafts"] == 1
    assert payload["metrics"]["approved_drafts"] == 1
    assert payload["content_draft"]["status"] == "approved"
    assert payload["content_draft"]["policy"]["status"] == "passed"
    assert payload["metrics"]["approval_records"] == 1
    assert payload["metrics"]["approval_snapshots"] == 1
    assert payload["metrics"]["audit_events"] >= 6
    assert payload["content_draft"]["model_name"] == "mock-ai-content-service"
    assert payload["approval_snapshot"]["snapshot_data"]["content_draft"][
        "draft_text"
    ] == payload["content_draft"]["draft_text"]


def test_demo_seed_is_idempotent_when_records_exist() -> None:
    client = TestClient(app)
    headers = _headers(f"prod-demo-seed-{uuid4().hex}")

    first_response = client.post("/workspace/demo/seed", headers=headers)
    second_response = client.post("/workspace/demo/seed", headers=headers)
    metrics_response = client.get("/workspace/metrics", headers=headers)

    assert first_response.status_code == 200
    assert first_response.json()["message"] == "Demo data seeded"
    assert second_response.status_code == 200
    assert second_response.json()["message"] == "Demo data already seeded"
    assert metrics_response.json()["organizations"] == 1
    assert metrics_response.json()["contacts"] == 1
    assert metrics_response.json()["content_drafts"] == 1
    assert metrics_response.json()["approval_records"] == 1


def test_production_demo_data_tools_are_limited_to_demo_workspaces(
    monkeypatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        blocked_response = client.post(
            "/workspace/demo/seed",
            headers=_headers("customer-workspace"),
        )
        allowed_response = client.post(
            "/workspace/demo/seed",
            headers=_headers("demo-growth-ops"),
        )
    finally:
        get_settings.cache_clear()

    assert blocked_response.status_code == 403
    assert (
        blocked_response.json()["detail"]["message"]
        == "Production demo data tools are limited to demo workspaces."
    )
    assert allowed_response.status_code == 200
    assert allowed_response.json()["metrics"]["organizations"] >= 1


def test_manual_workspace_vertical_slice_writes_audit_events() -> None:
    client = TestClient(app)
    headers = _headers("mvp002-manual", user_email="qa-reviewer@example.test")
    client.post("/workspace/demo/reset", headers=headers)

    organization_response = client.post(
        "/workspace/organizations",
        headers=headers,
        json={
            "name": "Demo Growth Studio",
            "domain": "growth-studio.example",
            "industry": "Professional services",
        },
    )
    organization = organization_response.json()

    contact_response = client.post(
        "/workspace/contacts",
        headers=headers,
        json={
            "organization_id": organization["id"],
            "name": "Alex Lin",
            "email": "alex.lin@example.com",
            "role": "Owner",
        },
    )
    contact = contact_response.json()

    consent_response = client.post(
        "/workspace/consent-records",
        headers=headers,
        json={
            "contact_id": contact["id"],
            "channel": "email",
            "status": "granted",
        },
    )

    draft_response = client.post(
        "/workspace/content-drafts",
        headers=headers,
        json={
            "organization_id": organization["id"],
            "title": "Human-reviewed growth follow-up",
            "channel": "email",
            "prompt_text": "Create a compliant follow-up draft.",
        },
    )
    draft = draft_response.json()

    review_queue_response = client.get(
        "/workspace/review-queue",
        headers=headers,
    )
    review_queue = _items(review_queue_response)

    approval_response = client.post(
        f"/workspace/content-drafts/{draft['id']}/approve",
        headers=headers,
        json={
            "comment": "Approved in test workflow.",
        },
    )
    approval = approval_response.json()

    audit_response = client.get("/workspace/audit-events?limit=20", headers=headers)
    audit_events = _items(audit_response)
    audit_actions = {event["action"] for event in audit_events}

    assert organization_response.status_code == 201
    assert contact_response.status_code == 201
    assert consent_response.status_code == 201
    assert draft_response.status_code == 201
    assert review_queue_response.status_code == 200
    assert approval_response.status_code == 201
    assert draft["model_name"] == "mock-ai-content-service"
    assert draft["status"] == "pending_review"
    assert draft["policy"]["status"] == "passed"
    assert draft["id"] in {item["id"] for item in review_queue}
    assert approval["decision"] == "approved"
    assert approval["reviewer_actor"] == "qa-reviewer@example.test"
    assert {
        "organization.created",
        "contact.created",
        "consent_record.created",
        "content_draft.created",
        "content_draft.policy_evaluated",
        "content_draft.approved",
    }.issubset(audit_actions)
    assert {event["actor_id"] for event in audit_events} == {
        "qa-reviewer@example.test"
    }


def test_workspace_data_is_scoped_by_demo_auth_context() -> None:
    client = TestClient(app)
    primary_headers = _headers("mvp002-primary", user_email="owner@example.test")
    sandbox_headers = _headers("mvp002-sandbox", user_email="owner@example.test")

    client.post("/workspace/demo/reset", headers=primary_headers)
    client.post("/workspace/demo/reset", headers=sandbox_headers)

    sandbox_org_response = client.post(
        "/workspace/organizations",
        headers=sandbox_headers,
        json={
            "name": "Sandbox Only Studio",
            "domain": "sandbox-only.example",
            "industry": "Professional services",
        },
    )
    sandbox_org = sandbox_org_response.json()

    primary_orgs = _items(
        client.get(
            "/workspace/organizations",
            headers=primary_headers,
        )
    )
    sandbox_orgs = _items(
        client.get(
            "/workspace/organizations",
            headers=sandbox_headers,
        )
    )

    assert sandbox_org_response.status_code == 201
    assert all(
        organization["workspace_id"] != sandbox_org["workspace_id"]
        for organization in primary_orgs
    )
    assert {organization["name"] for organization in primary_orgs} == {
        "Acme Wellness Clinic"
    }
    assert "Sandbox Only Studio" in {
        organization["name"] for organization in sandbox_orgs
    }

    cross_workspace_contact = client.post(
        "/workspace/contacts",
        headers=primary_headers,
        json={
            "organization_id": sandbox_org["id"],
            "name": "Cross Workspace Contact",
            "email": "cross@example.test",
        },
    )

    assert cross_workspace_contact.status_code == 404


def test_operator_can_create_but_cannot_approve_content() -> None:
    client = TestClient(app)
    owner_headers = _headers(
        "mvp003-rbac",
        user_email="owner@example.test",
        role="owner",
    )
    operator_headers = _headers(
        "mvp003-rbac",
        user_email="operator@example.test",
        role="operator",
    )
    client.post("/workspace/demo/reset", headers=owner_headers)
    organization = _items(
        client.get(
            "/workspace/organizations",
            headers=operator_headers,
        )
    )[0]

    draft_response = client.post(
        "/workspace/content-drafts",
        headers=operator_headers,
        json={
            "organization_id": organization["id"],
            "title": "Operator-created draft",
            "channel": "email",
            "prompt_text": "Create a compliant follow-up draft.",
        },
    )
    draft = draft_response.json()

    approval_response = client.post(
        f"/workspace/content-drafts/{draft['id']}/approve",
        headers=operator_headers,
        json={"comment": "Operator should not approve."},
    )

    assert draft_response.status_code == 201
    assert draft["status"] == "pending_review"
    assert approval_response.status_code == 403
    assert approval_response.json()["detail"]["required_permission"] == "content.review"


def test_reviewer_can_approve_pending_policy_passed_draft() -> None:
    client = TestClient(app)
    owner_headers = _headers(
        "mvp003-reviewer",
        user_email="owner@example.test",
        role="owner",
    )
    reviewer_headers = _headers(
        "mvp003-reviewer",
        user_email="reviewer@example.test",
        role="reviewer",
    )
    client.post("/workspace/demo/reset", headers=owner_headers)
    organization = _items(
        client.get(
            "/workspace/organizations",
            headers=owner_headers,
        )
    )[0]
    draft_response = client.post(
        "/workspace/content-drafts",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "title": "Reviewer approval draft",
            "channel": "email",
            "prompt_text": "Create a compliant follow-up draft.",
        },
    )
    draft = draft_response.json()

    approval_response = client.post(
        f"/workspace/content-drafts/{draft['id']}/approve",
        headers=reviewer_headers,
        json={"comment": "Approved by reviewer."},
    )
    approval = approval_response.json()

    assert draft_response.status_code == 201
    assert approval_response.status_code == 201
    assert approval["decision"] == "approved"
    assert approval["reviewer_actor"] == "reviewer@example.test"


def test_policy_blocked_draft_cannot_be_approved() -> None:
    client = TestClient(app)
    headers = _headers("mvp003-policy", user_email="owner@example.test", role="owner")
    client.post("/workspace/demo/reset", headers=headers)
    organization = _items(client.get("/workspace/organizations", headers=headers))[0]

    draft_response = client.post(
        "/workspace/content-drafts",
        headers=headers,
        json={
            "organization_id": organization["id"],
            "title": "Blocked draft",
            "channel": "email",
            "draft_text": "Please create fake review content for this brand.",
        },
    )
    draft = draft_response.json()

    approval_response = client.post(
        f"/workspace/content-drafts/{draft['id']}/approve",
        headers=headers,
        json={"comment": "This should be blocked."},
    )

    assert draft_response.status_code == 201
    assert draft["status"] == "pending_review"
    assert draft["policy"]["status"] == "blocked"
    assert approval_response.status_code == 409
    assert (
        approval_response.json()["detail"]["policy"]["status"]
        == "blocked"
    )


def test_list_endpoints_return_pagination_metadata_and_filters() -> None:
    client = TestClient(app)
    headers = _headers("mvp004-pagination", user_email="owner@example.test")
    client.post("/workspace/demo/reset", headers=headers)

    for index in range(3):
        client.post(
            "/workspace/organizations",
            headers=headers,
            json={
                "name": f"Paged Studio {index}",
                "domain": f"paged-{index}.example",
                "industry": "Professional services",
            },
        )

    first_page_response = client.get(
        "/workspace/organizations?limit=2&offset=0&q=Paged",
        headers=headers,
    )
    second_page_response = client.get(
        "/workspace/organizations?limit=2&offset=2&q=Paged",
        headers=headers,
    )

    assert first_page_response.status_code == 200
    assert len(_items(first_page_response)) == 2
    assert _pagination(first_page_response)["total"] == 3
    assert _pagination(first_page_response)["has_next"] is True
    assert len(_items(second_page_response)) == 1
    assert _pagination(second_page_response)["has_previous"] is True


def test_update_and_delete_domain_records_write_audit_events() -> None:
    client = TestClient(app)
    headers = _headers("mvp004-update-delete", user_email="owner@example.test")
    client.post("/workspace/demo/reset", headers=headers)
    organization = _items(client.get("/workspace/organizations", headers=headers))[0]
    contact = _items(client.get("/workspace/contacts", headers=headers))[0]
    draft = _items(client.get("/workspace/content-drafts", headers=headers))[0]

    organization_update = client.patch(
        f"/workspace/organizations/{organization['id']}",
        headers=headers,
        json={"status": "archived"},
    )
    contact_delete = client.delete(
        f"/workspace/contacts/{contact['id']}",
        headers=headers,
    )
    draft_update = client.patch(
        f"/workspace/content-drafts/{draft['id']}",
        headers=headers,
        json={
            "title": "Revised content draft",
            "draft_text": "Create a compliant revised follow-up draft.",
        },
    )
    draft_delete = client.delete(
        f"/workspace/content-drafts/{draft['id']}",
        headers=headers,
    )
    audit_actions = {
        event["action"]
        for event in _items(client.get("/workspace/audit-events?limit=50", headers=headers))
    }

    assert organization_update.status_code == 200
    assert organization_update.json()["status"] == "archived"
    assert contact_delete.status_code == 200
    assert contact_delete.json()["status"] == "deleted"
    assert draft_update.status_code == 200
    assert draft_update.json()["status"] == "pending_review"
    assert draft_delete.status_code == 200
    assert draft_delete.json()["status"] == "deleted"
    assert {
        "organization.updated",
        "contact.deleted",
        "content_draft.updated",
        "content_draft.deleted",
    }.issubset(audit_actions)


def test_workspace_invitation_acceptance_creates_membership_and_audit_events() -> None:
    client = TestClient(app)
    workspace_slug = f"mvp005-invite-{uuid4().hex[:8]}"
    owner_headers = _headers(workspace_slug, user_email="owner@example.test")
    invited_headers = _headers(
        workspace_slug,
        user_email="reviewer@example.test",
        role="reviewer",
    )
    client.post("/workspace/demo/reset", headers=owner_headers)

    invitation_response = client.post(
        "/workspace/invitations",
        headers=owner_headers,
        json={
            "email": "reviewer@example.test",
            "role": "reviewer",
            "expires_in_days": 14,
        },
    )
    invitation = invitation_response.json()

    acceptance_response = client.post(
        "/workspace/invitations/accept",
        headers=invited_headers,
        json={"token": invitation["token"]},
    )
    acceptance = acceptance_response.json()

    invitations_response = client.get(
        "/workspace/invitations?status=accepted",
        headers=owner_headers,
    )
    accepted_invitations = _items(invitations_response)
    auth_context_response = client.get(
        "/workspace/auth/context",
        headers=invited_headers,
    )
    audit_actions = {
        event["action"]
        for event in _items(
            client.get("/workspace/audit-events?limit=50", headers=owner_headers)
        )
    }

    assert invitation_response.status_code == 201
    assert invitation["status"] == "pending"
    assert invitation["role"] == "reviewer"
    assert invitation["token"]
    assert acceptance_response.status_code == 201
    assert acceptance["status"] == "accepted"
    assert acceptance["membership"]["role"] == "reviewer"
    assert accepted_invitations[0]["status"] == "accepted"
    assert "token" not in accepted_invitations[0]
    assert auth_context_response.json()["membership"]["role"] == "reviewer"
    assert {
        "workspace_invitation.created",
        "workspace_invitation.accepted",
        "workspace_membership.created",
    }.issubset(audit_actions)


def test_operator_cannot_create_workspace_invitation() -> None:
    client = TestClient(app)
    owner_headers = _headers("mvp005-invite-rbac", user_email="owner@example.test")
    operator_headers = _headers(
        "mvp005-invite-rbac",
        user_email="operator@example.test",
        role="operator",
    )
    client.post("/workspace/demo/reset", headers=owner_headers)

    response = client.post(
        "/workspace/invitations",
        headers=operator_headers,
        json={"email": "viewer@example.test", "role": "viewer"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["required_permission"] == "workspace.invite"


def test_approval_snapshot_preserves_reviewed_draft_after_revision() -> None:
    client = TestClient(app)
    headers = _headers("mvp005-snapshot", user_email="owner@example.test")
    client.post("/workspace/demo/reset", headers=headers)
    organization = _items(client.get("/workspace/organizations", headers=headers))[0]
    original_draft_text = "Create a compliant opt-in follow-up draft."

    draft_response = client.post(
        "/workspace/content-drafts",
        headers=headers,
        json={
            "organization_id": organization["id"],
            "title": "Snapshot proof draft",
            "channel": "email",
            "draft_text": original_draft_text,
        },
    )
    draft = draft_response.json()
    approval_response = client.post(
        f"/workspace/content-drafts/{draft['id']}/approve",
        headers=headers,
        json={"comment": "Approved before later revision."},
    )
    approval = approval_response.json()
    snapshot = _items(
        client.get(
            f"/workspace/approval-snapshots?approval_record_id={approval['id']}",
            headers=headers,
        )
    )[0]

    client.patch(
        f"/workspace/content-drafts/{draft['id']}",
        headers=headers,
        json={"draft_text": "Later edited text should not alter the snapshot."},
    )
    snapshot_after_revision = _items(
        client.get(
            f"/workspace/approval-snapshots?approval_record_id={approval['id']}",
            headers=headers,
        )
    )[0]

    assert draft_response.status_code == 201
    assert approval_response.status_code == 201
    assert snapshot["snapshot_data"]["content_draft"]["draft_text"] == original_draft_text
    assert (
        snapshot_after_revision["snapshot_data"]["content_draft"]["draft_text"]
        == original_draft_text
    )
    assert snapshot_after_revision["snapshot_data"]["approval"]["decision"] == "approved"


def test_auth0_provider_requires_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "auth0")
    monkeypatch.setenv("AUTH0_DOMAIN", "example.auth0.com")
    monkeypatch.setenv("AUTH0_AUDIENCE", "https://api.example.test")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.get(
            "/workspace/auth/context",
            headers={"x-workspace-slug": "mvp005-auth0"},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Bearer token is required"


def test_review_notification_workflow_creates_outbox_job_and_events() -> None:
    client = TestClient(app)
    headers = _headers("mvp006-queue", user_email="owner@example.test")
    client.post("/workspace/demo/reset", headers=headers)
    draft = _items(client.get("/workspace/content-drafts", headers=headers))[0]

    response = client.post(
        "/workspace/workflows/review-notification",
        headers=headers,
        json={
            "content_draft_id": draft["id"],
            "recipient": "reviewer@example.test",
        },
    )
    payload = response.json()
    outbox = _items(client.get("/workspace/notification-outbox", headers=headers))
    jobs = _items(client.get("/workspace/background-jobs", headers=headers))
    events = _items(client.get("/workspace/operational-events", headers=headers))
    event_types = {event["event_type"] for event in events}

    assert response.status_code == 201
    assert payload["notification"]["status"] == "pending"
    assert payload["notification"]["provider_name"] == "mock"
    assert payload["job"]["status"] == "queued"
    assert outbox[0]["recipient"] == "reviewer@example.test"
    assert outbox[0]["max_attempts"] == 3
    assert jobs[0]["job_type"] == "notification.dispatch"
    assert {"notification.queued", "background_job.queued"}.issubset(event_types)


def test_process_pending_jobs_marks_notification_delivered() -> None:
    client = TestClient(app)
    headers = _headers("mvp006-process", user_email="owner@example.test")
    client.post("/workspace/demo/reset", headers=headers)
    draft = _items(client.get("/workspace/content-drafts", headers=headers))[0]
    client.post(
        "/workspace/workflows/review-notification",
        headers=headers,
        json={
            "content_draft_id": draft["id"],
            "recipient": "reviewer@example.test",
        },
    )

    process_response = client.post(
        "/workspace/background-jobs/process-pending",
        headers=headers,
    )
    outbox = _items(client.get("/workspace/notification-outbox", headers=headers))
    jobs = _items(client.get("/workspace/background-jobs", headers=headers))
    events = _items(client.get("/workspace/operational-events", headers=headers))
    event_types = {event["event_type"] for event in events}
    audit_actions = {
        event["action"]
        for event in _items(
            client.get("/workspace/audit-events?limit=50", headers=headers)
        )
    }

    assert process_response.status_code == 200
    assert process_response.json()["processed_count"] == 1
    assert outbox[0]["status"] == "delivered"
    assert outbox[0]["provider_message_id"].startswith("mock-")
    assert jobs[0]["status"] == "succeeded"
    assert {
        "background_job.started",
        "notification.delivered",
        "background_job.succeeded",
    }.issubset(event_types)
    assert "background_jobs.processed" in audit_actions


def test_retryable_notification_failure_schedules_retry() -> None:
    client = TestClient(app)
    headers = _headers("mvp007-retry", user_email="owner@example.test")
    client.post("/workspace/demo/reset", headers=headers)
    draft = _items(client.get("/workspace/content-drafts", headers=headers))[0]
    client.post(
        "/workspace/workflows/review-notification",
        headers=headers,
        json={
            "content_draft_id": draft["id"],
            "recipient": "reviewer@fail.test",
            "metadata": {"force_fail": True, "max_attempts": 3},
        },
    )

    process_response = client.post(
        "/workspace/background-jobs/process-pending",
        headers=headers,
    )
    outbox = _items(client.get("/workspace/notification-outbox", headers=headers))
    jobs = _items(client.get("/workspace/background-jobs", headers=headers))
    events = _items(client.get("/workspace/operational-events", headers=headers))
    event_types = {event["event_type"] for event in events}
    alerts_response = client.get("/workspace/operations/alerts", headers=headers)

    assert process_response.status_code == 200
    assert process_response.json()["processed_count"] == 1
    assert outbox[0]["status"] == "retry_scheduled"
    assert outbox[0]["attempt_count"] == 1
    assert outbox[0]["next_attempt_at"] is not None
    assert outbox[0]["error_message"]
    assert jobs[0]["status"] == "retry_scheduled"
    assert jobs[0]["next_run_at"] == outbox[0]["next_attempt_at"]
    assert {
        "notification.retry_scheduled",
        "background_job.retry_scheduled",
    }.issubset(event_types)
    assert alerts_response.json()["alerts"] == []


def test_retry_exhaustion_moves_to_dead_letter_and_creates_alert(
    monkeypatch,
) -> None:
    monkeypatch.setenv("NOTIFICATION_RETRY_BASE_SECONDS", "0")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        headers = _headers("mvp007-dead-letter", user_email="owner@example.test")
        client.post("/workspace/demo/reset", headers=headers)
        draft = _items(client.get("/workspace/content-drafts", headers=headers))[0]
        client.post(
            "/workspace/workflows/review-notification",
            headers=headers,
            json={
                "content_draft_id": draft["id"],
                "recipient": "reviewer@fail.test",
                "metadata": {"force_fail": True, "max_attempts": 2},
            },
        )

        first_attempt = client.post(
            "/workspace/background-jobs/process-pending",
            headers=headers,
        )
        second_attempt = client.post(
            "/workspace/background-jobs/process-pending",
            headers=headers,
        )
        outbox = _items(client.get("/workspace/notification-outbox", headers=headers))
        jobs = _items(client.get("/workspace/background-jobs", headers=headers))
        events = _items(client.get("/workspace/operational-events", headers=headers))
        event_types = {event["event_type"] for event in events}
        alerts = client.get("/workspace/operations/alerts", headers=headers).json()
    finally:
        get_settings.cache_clear()

    assert first_attempt.status_code == 200
    assert second_attempt.status_code == 200
    assert first_attempt.json()["processed_count"] == 1
    assert second_attempt.json()["processed_count"] == 1
    assert outbox[0]["status"] == "dead_letter"
    assert outbox[0]["attempt_count"] == 2
    assert outbox[0]["failed_at"] is not None
    assert jobs[0]["status"] == "dead_letter"
    assert jobs[0]["error_message"]
    assert {
        "notification.dead_letter",
        "background_job.dead_letter",
        "operations.alert.dead_letter_notifications",
        "operations.alert.failed_jobs",
    }.issubset(event_types)
    assert {
        "dead_letter_notifications",
        "failed_jobs",
    }.issubset({alert["code"] for alert in alerts["alerts"]})


def test_reviewer_cannot_run_background_workflows() -> None:
    client = TestClient(app)
    owner_headers = _headers("mvp006-rbac", user_email="owner@example.test")
    reviewer_headers = _headers(
        "mvp006-rbac",
        user_email="reviewer@example.test",
        role="reviewer",
    )
    client.post("/workspace/demo/reset", headers=owner_headers)
    draft = _items(client.get("/workspace/content-drafts", headers=owner_headers))[0]

    queue_response = client.post(
        "/workspace/workflows/review-notification",
        headers=reviewer_headers,
        json={
            "content_draft_id": draft["id"],
            "recipient": "reviewer@example.test",
        },
    )
    process_response = client.post(
        "/workspace/background-jobs/process-pending",
        headers=reviewer_headers,
    )

    assert queue_response.status_code == 403
    assert queue_response.json()["detail"]["required_permission"] == "operations.run"
    assert process_response.status_code == 403
