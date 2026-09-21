"""Wave 0 Tracer Bullet & Spine Contract Verification Suite (tests/unit/test_tracer_bullet.py)."""

import json
import pathlib
import yaml

from fastapi.testclient import TestClient

from app.agent import root_agent
from app.core.config import settings
from app.core.database import get_db_session
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


def test_all_five_pod_agent_tools_auto_discovered() -> None:
    """Verifies that root_agent auto-discovers all 5 independent pod AgentTools."""
    assert len(root_agent.tools) == 6  # 1 tracer bullet tool + 5 pod AgentTools


def test_all_five_pod_routers_auto_mounted() -> None:
    """Verifies that all 5 isolated pod status routes respond independently on the Spine."""
    for pod_slug in [
        "pod1_security_privacy",
        "pod2_policy_rag",
        "pod3_workweek_leave",
        "pod4_it_saga",
        "pod5_escalation_evals",
    ]:
        resp = client.get(f"/api/v1/{pod_slug}/status")
        assert resp.status_code == 200
        assert resp.json() == {"pod": pod_slug, "status": "READY"}


def test_sse_chat_stream_emits_zdr_header_and_events() -> None:
    """Verifies that POST /api/v1/chat/stream emits typed SSE events and ZDR headers."""
    resp = client.post(
        "/api/v1/chat/stream",
        json={"message": "Check my PTO balance", "widget_hint": "hitl_card"},
        headers={"x-employee-sub": "EMP-1042", "x-country-code": "US", "x-employee-role": "IC"},
    )
    assert resp.status_code == 200
    assert resp.headers["x-vertex-ai-zero-data-retention"] == "true"
    assert "event: metadata" in resp.text
    assert "event: token" in resp.text
    assert "event: widget" in resp.text
    assert "event: done" in resp.text


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


def test_database_session_dependency_callable() -> None:
    """Verifies that the async PostgreSQL 16 session generator is importable for Pod routers."""
    assert callable(get_db_session)


def test_agents_cli_eval_structure_and_schema_valid() -> None:
    """Verifies the prescribed agents-cli tests/eval/ directory and canonical dataset schemas."""
    eval_dir = pathlib.Path("tests/eval")
    config_file = eval_dir / "eval_config.yaml"
    report_file = eval_dir / "evaluation_report.md"
    single_turn_file = eval_dir / "datasets" / "eval-single-turn.json"
    multi_turn_file = eval_dir / "datasets" / "eval-multi-turn.json"

    assert config_file.is_file()
    assert report_file.is_file()
    assert single_turn_file.is_file()
    assert multi_turn_file.is_file()

    cfg = yaml.safe_load(config_file.read_text())
    assert "metrics_to_run" in cfg
    assert "custom_metrics" in cfg
    assert all("prompt_template" in m for m in cfg["custom_metrics"])

    single_data = json.loads(single_turn_file.read_text())
    assert len(single_data["eval_cases"]) >= 4
    for case in single_data["eval_cases"]:
        assert "prompt" in case
        assert "response" in case["reference"]
        assert "response" in case["responses"][0]

    multi_data = json.loads(multi_turn_file.read_text())
    assert len(multi_data["eval_cases"]) >= 3
    for case in multi_data["eval_cases"]:
        assert "agent_data" in case
        assert "agents" in case["agent_data"]
        assert "turns" in case["agent_data"]


def test_cloud_run_dockerfile_and_env_example_present() -> None:
    """Verifies Cloud Run Dockerfile (--no-dev exclusion of tests/) and .env.example."""
    dockerfile = pathlib.Path("Dockerfile")
    env_example = pathlib.Path(".env.example")
    dockerignore = pathlib.Path(".dockerignore")

    assert dockerfile.is_file()
    assert env_example.is_file()
    assert dockerignore.is_file()

    dockerfile_text = dockerfile.read_text()
    assert "--no-dev" in dockerfile_text
    assert "USER appuser" in dockerfile_text
    assert "tests/" in dockerignore.read_text()
