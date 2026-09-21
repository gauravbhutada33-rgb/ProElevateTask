"""Two-Phase HITL Proposal Service & PostgreSQL 16 Repository Integration (app/slices/pod3_workweek_leave/hitl_service.py)."""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.mcp_client import PENDING_HITL_PROPOSALS
from app.core.models import HITLProposal
from app.slices.pod3_workweek_leave.repository import (
    HITLProposalRepository,
    clear_repository_state,
)
from app.slices.pod3_workweek_leave.workweek_client import (
    commit_leave_to_workweek,
    get_leave_balance,
)

HITL_TTL_MINUTES = 15
HITL_TTL_SECONDS = HITL_TTL_MINUTES * 60


class DuplicateProposalError(ValueError):
    """Raised when an identical active proposal already exists within the 15-minute TTL window."""


class ProposalNotFoundError(KeyError):
    """Raised when a proposal_id does not exist."""


class ProposalExpiredError(ValueError):
    """Raised when a human confirmation arrives after the 15-minute TTL has expired."""


class UnauthorizedProposalOwnerError(PermissionError):
    """Raised when the Okta JWT subject does not match proposal.employee_id."""


def clear_proposal_store() -> None:
    """Clears in-memory proposal repository state for deterministic test isolation."""
    clear_repository_state()


def get_proposal_by_id(proposal_id: str) -> HITLProposal | None:
    """Retrieves a tracked HITLProposal by proposal_id."""
    from app.slices.pod3_workweek_leave.repository import _PROPOSALS_BY_ID

    return _PROPOSALS_BY_ID.get(str(proposal_id))


def compute_leave_idempotency_key(
    employee_id: str,
    start_date: str,
    end_date: str,
    days: float,
    leave_type: str,
) -> str:
    """Computes deterministic SHA-256 idempotency key for leave request proposals."""
    canonical = f"{employee_id}:propose_leave_request:{start_date}:{end_date}:{days}:{leave_type}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def propose_leave_request(
    employee_id: str = settings.DEFAULT_EMPLOYEE_ID,
    start_date: str = "2026-11-23",
    end_date: str = "2026-11-25",
    days: float = 3.0,
    leave_type: str = "PTO",
    session_id: UUID | None = None,
    db_session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Phase 1 (Agent Tool Callable): Creates a 15-min TTL PENDING proposal in hitl_proposals."""
    now = datetime.now(UTC)
    repo = HITLProposalRepository(db_session=db_session)
    idempotency_key = compute_leave_idempotency_key(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        leave_type=leave_type,
    )

    existing = await repo.get_active_by_idempotency_key(idempotency_key, now=now)
    if existing is not None:
        raise DuplicateProposalError(
            f"Duplicate leave proposal blocked within 15-minute window (proposal_id={existing.proposal_id})."
        )

    balance = await get_leave_balance(employee_id)
    remaining_balance = max(0.0, round(balance.pto_available_days - float(days), 2))
    expires_at = now + timedelta(minutes=HITL_TTL_MINUTES)
    proposal_uuid = uuid4()

    proposed_payload: dict[str, Any] = {
        "employee_id": employee_id,
        "start_date": start_date,
        "end_date": end_date,
        "days": float(days),
        "leave_type": leave_type,
        "remaining_balance": remaining_balance,
    }

    proposal = HITLProposal(
        proposal_id=proposal_uuid,
        session_id=session_id or uuid4(),
        employee_id=employee_id,
        tool_name="propose_leave_request",
        proposed_payload=proposed_payload,
        idempotency_key=idempotency_key,
        status="PENDING",
        expires_at=expires_at,
        created_at=now,
    )

    await repo.save(proposal)
    proposal_id_str = str(proposal_uuid)

    # Also sync with Spine PENDING_HITL_PROPOSALS registry
    PENDING_HITL_PROPOSALS[proposal_id_str] = {
        "proposal_id": proposal_id_str,
        "employee_id": employee_id,
        "target_mcp": "WorkWeek",
        "mcp_tool_name": "request_time_off",
        "arguments": {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": leave_type,
            "days": float(days),
        },
        "idempotency_key": idempotency_key,
        "status": "PENDING",
        "expires_at_utc": expires_at.isoformat(),
    }

    hitl_card: dict[str, Any] = {
        "type": "hitl_card",
        "proposal_id": proposal_id_str,
        "employee_id": employee_id,
        "tool_name": "propose_leave_request",
        "start_date": start_date,
        "end_date": end_date,
        "days": float(days),
        "leave_type": leave_type,
        "remaining_balance": remaining_balance,
        "status": "PENDING",
        "ttl_seconds": HITL_TTL_SECONDS,
        "expires_at": expires_at.isoformat(),
    }

    return {
        "proposal_id": proposal_id_str,
        "idempotency_key": idempotency_key,
        "status": "PENDING",
        "expires_at": expires_at.isoformat(),
        "hitl_card": hitl_card,
        "message": (
            f"I have prepared a draft {leave_type} request (`proposal_id: {proposal_id_str}`) "
            f"for **{days} days ({start_date} to {end_date})** (remaining balance: {remaining_balance} days). "
            "Please review and click **Confirm** on the confirmation card within 15 minutes "
            "to submit this request to WorkWeek."
        ),
    }


async def confirm_leave_proposal(
    proposal_id: str,
    jwt_subject: str,
    decision: str = "CONFIRM",
    simulate_http_status: int | None = None,
    retry_after_seconds: int | None = None,
    db_session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Phase 2 (Human REST Endpoint Only): Validates JWT subject & 15m TTL before committing."""
    repo = HITLProposalRepository(db_session=db_session)
    proposal = await repo.get_by_id(str(proposal_id))
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal '{proposal_id}' not found.")

    if jwt_subject != proposal.employee_id:
        raise UnauthorizedProposalOwnerError("JWT subject mismatch with proposal owner.")

    now = datetime.now(UTC)
    if proposal.expires_at <= now:
        proposal.status = "EXPIRED"
        await repo.save(proposal)
        raise ProposalExpiredError(f"Proposal '{proposal_id}' expired at {proposal.expires_at.isoformat()}.")

    if decision.upper() != "CONFIRM":
        proposal.status = "REJECTED"
        await repo.save(proposal)
        return {
            "proposal_id": str(proposal.proposal_id),
            "status": "REJECTED",
            "confirmed_by": jwt_subject,
            "confirmed_at_utc": now.isoformat(),
        }

    commit_result = await commit_leave_to_workweek(
        proposal=proposal,
        simulate_http_status=simulate_http_status,
        retry_after_seconds=retry_after_seconds,
    )
    await repo.save(proposal)
    if str(proposal_id) in PENDING_HITL_PROPOSALS:
        PENDING_HITL_PROPOSALS[str(proposal_id)]["status"] = commit_result.status
    return {
        "proposal_id": str(proposal.proposal_id),
        "status": commit_result.status,
        "workweek_transaction_id": commit_result.workweek_transaction_id,
        "queue_name": commit_result.queue_name,
        "task_id": commit_result.task_id,
        "retry_after_seconds": commit_result.retry_after_seconds,
        "confirmed_by": jwt_subject,
        "confirmed_at_utc": commit_result.committed_at_utc,
    }
