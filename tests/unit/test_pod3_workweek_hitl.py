"""Pod 3 Unit, Rate-Limit & PostgreSQL 16 HITL Proposal Contract Tests (tests/unit/test_pod3_workweek_hitl.py)."""

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.fast_api_app import app
from app.slices.pod3_workweek_leave.hitl_service import (
    DuplicateProposalError,
    ProposalExpiredError,
    clear_proposal_store,
    confirm_leave_proposal,
    get_proposal_by_id,
    propose_leave_request,
)
from app.slices.pod3_workweek_leave.repository import HITLProposalRepository
from app.slices.pod3_workweek_leave.sub_agent import (
    HRISActionAgent,
    get_agent_tool,
    hris_agent_tool,
    pod3_agent_tool,
    specialist_agent,
)
from app.slices.pod3_workweek_leave.workweek_client import (
    clear_balance_cache_and_retry_queue,
    commit_leave_to_workweek,
    get_cached_balance_ttl,
    get_leave_balance,
    get_queued_retry_tasks,
    set_redis_client,
    workweek_limiter,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_pod3_state() -> None:
    """Ensures deterministic state isolation across all Pod 3 unit tests."""
    clear_proposal_store()
    clear_balance_cache_and_retry_queue()


def test_pod3_status_endpoint() -> None:
    """Verifies Pod 3 router health endpoint."""
    response = client.get("/api/v1/pod3_workweek_leave/status")
    assert response.status_code == 200
    assert response.json() == {"pod": "pod3_workweek_leave", "status": "READY"}


def test_hris_action_agent_hallucination_firewall() -> None:
    """GOV-03 Firewall: HRISActionAgent may ONLY call get_leave_balance and propose_leave_request."""
    assert specialist_agent.name == "hris_action_agent"
    assert HRISActionAgent.name == "hris_action_agent"
    assert specialist_agent.model == settings.GEMINI_FLASH_MODEL

    tool_names = {getattr(t, "__name__", getattr(t, "name", str(t))) for t in (specialist_agent.tools or [])}
    assert "get_leave_balance" in tool_names
    assert "propose_leave_request" in tool_names
    assert "commit_leave_request" not in tool_names
    assert "commit_leave_to_workweek" not in tool_names

    agent_tool = get_agent_tool()
    assert agent_tool.agent.name == "hris_action_agent"
    assert hris_agent_tool.agent.name == "hris_action_agent"
    assert pod3_agent_tool.agent.name == "hris_action_agent"


async def test_workweek_limiter_and_redis_cache_sla() -> None:
    """RES-02 & SLA-02: Verifies 50 RPS AsyncLimiter, 60s Redis cache TTL, and <60s webhook invalidation."""
    assert workweek_limiter.max_rate == 50
    assert workweek_limiter.time_period == 1.0

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    set_redis_client(mock_redis)

    balance = await get_leave_balance("EMP-1042")
    assert balance.employee_id == "EMP-1042"
    assert balance.pto_available_days > 0
    assert get_cached_balance_ttl("EMP-1042") == 60
    mock_redis.setex.assert_awaited_once()
    assert mock_redis.setex.call_args.args[0] == "ww:balance:EMP-1042"
    assert mock_redis.setex.call_args.args[1] == 60

    # Canonical POST /api/v1/webhooks/workweek eviction must call redis.delete("ww:balance:EMP-1042") in <60s
    webhook_resp = client.post(
        "/api/v1/webhooks/workweek",
        json={"employee_id": "EMP-1042", "event_type": "BALANCE_UPDATED"},
    )
    assert webhook_resp.status_code == 200
    assert webhook_resp.json()["evicted_key"] == "ww:balance:EMP-1042"
    mock_redis.delete.assert_awaited_with("ww:balance:EMP-1042")
    assert get_cached_balance_ttl("EMP-1042") is None


async def test_propose_leave_request_two_phase_hitl_and_idempotency() -> None:
    """GOV-03: Verifies SHA-256 idempotency key, 15m TTL, hitl_card payload, and duplicate guard."""
    result = await propose_leave_request(
        employee_id="EMP-1042",
        start_date="2026-11-23",
        end_date="2026-11-25",
        days=3.0,
        leave_type="PTO",
    )

    expected_hash = hashlib.sha256(
        b"EMP-1042:propose_leave_request:2026-11-23:2026-11-25:3.0:PTO"
    ).hexdigest()

    assert result["status"] == "PENDING"
    assert result["idempotency_key"] == expected_hash
    assert result["hitl_card"]["type"] == "hitl_card"
    assert result["hitl_card"]["start_date"] == "2026-11-23"
    assert result["hitl_card"]["end_date"] == "2026-11-25"
    assert result["hitl_card"]["days"] == 3.0
    assert result["hitl_card"]["leave_type"] == "PTO"
    assert result["hitl_card"]["ttl_seconds"] == 900

    proposal = get_proposal_by_id(result["proposal_id"])
    assert proposal is not None
    assert proposal.status == "PENDING"
    assert proposal.idempotency_key == expected_hash

    # Duplicate proposal within 15-minute window must raise DuplicateProposalError
    with pytest.raises(DuplicateProposalError):
        await propose_leave_request(
            employee_id="EMP-1042",
            start_date="2026-11-23",
            end_date="2026-11-25",
            days=3.0,
            leave_type="PTO",
        )


async def test_confirm_hitl_proposal_jwt_mismatch_and_ttl_expiry() -> None:
    """GOV-03: Verifies JWT sub == employee_id enforcement, 15m TTL expiration, and human CONFIRM on /api/v1/hitl/confirm."""
    proposed = await propose_leave_request(
        employee_id="EMP-1042",
        start_date="2026-12-01",
        end_date="2026-12-02",
        days=2.0,
        leave_type="PTO",
    )
    proposal_id = proposed["proposal_id"]

    # 1. Cross-user JWT subject mismatch on /api/v1/hitl/confirm must fail with HTTP 403
    mismatch_resp = client.post(
        "/api/v1/hitl/confirm",
        json={"proposal_id": proposal_id, "employee_id": "EMP-1042", "decision": "CONFIRM"},
        headers={"x-employee-sub": "EMP-9999"},
    )
    assert mismatch_resp.status_code == 403

    # 2. Valid human confirmation on /api/v1/hitl/confirm transitions proposal to CONFIRMED
    confirm_resp = client.post(
        "/api/v1/hitl/confirm",
        json={"proposal_id": proposal_id, "employee_id": "EMP-1042", "decision": "CONFIRM"},
        headers={"x-employee-sub": "EMP-1042"},
    )
    assert confirm_resp.status_code == 200
    body = confirm_resp.json()
    assert body["status"] == "CONFIRMED"
    assert body["proposal_id"] == proposal_id
    assert body["workweek_transaction_id"].startswith("WW-TX-")

    # 3. Expired proposal (expires_at <= now) must transition to EXPIRED and reject confirmation
    expired_draft = await propose_leave_request(
        employee_id="EMP-1042",
        start_date="2026-12-10",
        end_date="2026-12-11",
        days=2.0,
        leave_type="PTO",
    )
    expired_obj = get_proposal_by_id(expired_draft["proposal_id"])
    assert expired_obj is not None
    expired_obj.expires_at = datetime.now(UTC) - timedelta(seconds=5)

    with pytest.raises(ProposalExpiredError):
        await confirm_leave_proposal(
            proposal_id=expired_draft["proposal_id"],
            jwt_subject="EMP-1042",
            decision="CONFIRM",
        )
    assert expired_obj.status == "EXPIRED"


async def test_workweek_429_and_5xx_cloud_tasks_retry_queue() -> None:
    """RES-02: On HTTP 429 or 5xx, transition status to QUEUED_RETRY and enqueue to ww-it-mutation-retry-queue."""
    proposed = await propose_leave_request(
        employee_id="EMP-1042",
        start_date="2026-12-20",
        end_date="2026-12-24",
        days=5.0,
        leave_type="PTO",
    )
    proposal = get_proposal_by_id(proposed["proposal_id"])
    assert proposal is not None

    commit_result = await commit_leave_to_workweek(
        proposal,
        simulate_http_status=429,
        retry_after_seconds=12,
    )

    assert commit_result.status == "QUEUED_RETRY"
    assert proposal.status == "QUEUED_RETRY"
    assert commit_result.queue_name == "ww-it-mutation-retry-queue"
    assert commit_result.retry_after_seconds == 12

    queued_tasks = get_queued_retry_tasks()
    assert len(queued_tasks) == 1
    task = queued_tasks[0]
    assert task["queue_name"] == "ww-it-mutation-retry-queue"
    assert task["idempotency_key"] == proposal.idempotency_key
    assert task["max_attempts"] == 5
    assert task["initial_backoff_seconds"] == 2
    assert task["max_backoff_seconds"] == 60


async def test_sqlalchemy_async_session_persistence_and_multi_turn_eval_signature() -> None:
    """Verifies SQLAlchemy 2.0 AsyncSession repository persistence and eval-multi-turn signature."""
    from unittest.mock import MagicMock

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_exec_result = MagicMock()
    mock_exec_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_exec_result

    # Call without employee_id exactly as specified in eval-multi-turn.json
    eval_turn1 = await propose_leave_request(
        start_date="2026-11-23",
        end_date="2026-11-25",
        days=3.0,
        leave_type="PTO",
        db_session=mock_db,
    )
    assert eval_turn1["status"] == "PENDING"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

    repo = HITLProposalRepository(db_session=mock_db)
    audit_log = await repo.record_audit_log(
        pseudonym_hash="a" * 64,
        action_type="LEAVE_PROPOSAL_CREATED",
        status="PENDING",
        metadata_json={"proposal_id": eval_turn1["proposal_id"]},
    )
    assert audit_log.target_system == "WORKWEEK_HRIS"
