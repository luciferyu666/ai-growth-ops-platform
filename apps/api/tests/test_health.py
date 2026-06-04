from sqlalchemy import text

from app.db import get_session
from fastapi.testclient import TestClient

from app.main import app


def test_health_route_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_deep_health_checks_database_and_redis() -> None:
    client = TestClient(app)

    response = client.get("/health/deep")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["checks"]["database"]["status"] == "ok"
    assert payload["checks"]["redis"]["status"] == "ok"


def test_database_session_executes_select_one() -> None:
    session_generator = get_session()
    session = next(session_generator)

    try:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        session_generator.close()


def test_proposal_demo_returns_technical_demo_payload() -> None:
    client = TestClient(app)

    response = client.get("/proposal/demo")
    payload = response.json()

    assert response.status_code == 200
    assert payload["title"] == "Technical Proposal Demo"
    assert payload["positioning"]["primary"]
    assert len(payload["readiness"]) >= 4
    assert len(payload["roadmap"]) >= 4
    assert "Fake reviews" in payload["compliance_boundary"]["excluded"]
