"""Wave 0 Tracer Bullet Unit & Contract Verification Suite (tests/unit/test_tracer_bullet.py)."""

from fastapi.testclient import TestClient

from app.agent import root_agent, tracer_bullet_health_check
from app.core.config import settings
from app.core.models import Base
from app.fast_api_app import app

client = TestClient(app)


def test_gemini_3_6_models_and_zdr_locked() -> None:
    """Verifies that Gemini 3.6 Flash and Gemini 3.6 Pro are locked with Vertex AI ZDR."""
    assert settings.GEMINI_FLASH_MODEL == "gemini-3.6-flash"
    assert settings.GEMINI_PRO_MODEL == "gemini-3.6-pro"
    assert settings.VERTEX_AI_ZERO_DATA_RETENTION is True
    assert root_agent.model == "gemini-3.6-pro"


def test_six_core_postgresql_tables_registered() -> None:
    """Verifies that all 6 canonical PostgreSQL 16 tables are registered in SQLAlchemy metadata."""
    expected_tables = {
        "user_salts",
        "sessions",
        "conversation_turns",
        "hitl_proposals",
        "audit_trail_logs",
        "hr_policy_chunks",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))


def test_hitl_jwt_subject_mismatch_blocked() -> None:
    """Verifies that /api/v1/hitl/confirm blocks cross-user confirmation attempts."""
    response = client.post(
        "/api/v1/hitl/confirm",
        json={"proposal_id": "prop-123", "employee_id": "EMP-1042", "decision": "CONFIRM"},
        headers={"x-employee-sub": "EMP-9999"},
    )
    assert response.status_code == 403


def test_gdpr_art17_forget_me_issues_erasure_receipt() -> None:
    """Verifies that DELETE /api/v1/privacy/forget-me returns a cryptographic erasure receipt."""
    response = client.delete(
        "/api/v1/privacy/forget-me",
        headers={"x-employee-sub": "EMP-1042"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CRYPTO_SHREDDED"
    assert body["erasure_receipt_id"].startswith("ERASURE-")
