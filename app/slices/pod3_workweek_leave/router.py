"""Isolated FastAPI Router for pod3_workweek_leave — auto-mounted by app/fast_api_app.py."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.mcp_client import commit_confirmed_hitl_proposal
from app.slices.pod3_workweek_leave.hitl_service import (
    ProposalExpiredError,
    ProposalNotFoundError,
    UnauthorizedProposalOwnerError,
    confirm_leave_proposal,
    get_proposal_by_id,
)
from app.slices.pod3_workweek_leave.workweek_client import evict_leave_balance_cache

router = APIRouter(tags=["pod3_workweek_leave"])


class Pod3HITLConfirmRequest(BaseModel):
    """Request payload for human confirmation of a pending WorkWeek leave proposal."""

    proposal_id: str
    employee_id: str
    decision: str = "CONFIRM"
    simulate_http_status: int | None = None
    retry_after_seconds: int | None = None


class WorkWeekWebhookPayload(BaseModel):
    """Webhook payload emitted by WorkWeek HRIS when employee leave balances change."""

    employee_id: str
    event_type: str = "BALANCE_UPDATED"


@router.get("/api/v1/pod3_workweek_leave/status")
async def pod_status() -> dict[str, str]:
    """Independent health check for pod3_workweek_leave."""
    return {"pod": "pod3_workweek_leave", "status": "READY"}


@router.post("/api/v1/pod3_workweek_leave/hitl/confirm")
@router.post("/api/v1/hitl/confirm")
async def confirm_pod3_leave_proposal(
    payload: Pod3HITLConfirmRequest,
    x_employee_sub: str = Header(..., description="Verified Okta OIDC JWT subject claim"),
) -> dict[str, Any]:
    """GOV-03 Phase 2: Human REST Endpoint validating JWT sub == employee_id and 15m TTL before committing."""
    if x_employee_sub != payload.employee_id:
        raise HTTPException(status_code=403, detail="JWT subject mismatch with proposal owner.")

    tracked = get_proposal_by_id(payload.proposal_id)
    if tracked is None:
        if payload.decision.upper() == "CONFIRM":
            mcp_result = await commit_confirmed_hitl_proposal(payload.proposal_id)
            return {
                "proposal_id": payload.proposal_id,
                "status": "CONFIRMED",
                "confirmed_by": x_employee_sub,
                "mcp_execution": mcp_result,
                "confirmed_at_utc": datetime.now(UTC).isoformat(),
            }
        return {
            "proposal_id": payload.proposal_id,
            "status": "REJECTED",
            "confirmed_by": x_employee_sub,
            "confirmed_at_utc": datetime.now(UTC).isoformat(),
        }

    try:
        return await confirm_leave_proposal(
            proposal_id=payload.proposal_id,
            jwt_subject=x_employee_sub,
            decision=payload.decision,
            simulate_http_status=payload.simulate_http_status,
            retry_after_seconds=payload.retry_after_seconds,
        )
    except UnauthorizedProposalOwnerError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ProposalExpiredError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/v1/pod3_workweek_leave/webhooks/workweek")
@router.post("/api/v1/webhooks/workweek")
async def workweek_balance_webhook(payload: WorkWeekWebhookPayload) -> dict[str, str]:
    """SLA-02: Evicts `ww:balance:{employee_id}` in <60s when WorkWeek leave balances update."""
    evicted_key = await evict_leave_balance_cache(payload.employee_id)
    return {
        "status": "CACHE_EVICTED",
        "employee_id": payload.employee_id,
        "evicted_key": evicted_key,
        "evicted_at_utc": datetime.now(UTC).isoformat(),
    }
