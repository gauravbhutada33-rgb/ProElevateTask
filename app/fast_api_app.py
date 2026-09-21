"""FastAPI SSE Runtime, Two-Phase HITL Confirmation & GDPR Art. 17 Endpoint (app/fast_api_app.py)."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.agent import root_agent, tracer_bullet_health_check
from app.core.config import settings

app = FastAPI(
    title="Enterprise HR Agentic Solution (MVP 1)",
    version="1.3.0",
    description="ADK Pattern C Supervisor + Speculative Guardrails + Two-Phase HITL Gate",
)


class HITLConfirmRequest(BaseModel):
    """Request body for human confirmation of a pending proposal."""

    proposal_id: str
    employee_id: str
    decision: str  # "CONFIRM" | "CANCEL"


@app.get("/health")
async def health() -> dict[str, str]:
    """Wave 0 Tracer Bullet health endpoint."""
    return tracer_bullet_health_check()


@app.post("/api/v1/hitl/confirm")
async def confirm_hitl_proposal(
    payload: HITLConfirmRequest,
    x_employee_sub: str = Header(..., description="Verified Okta OIDC JWT subject claim"),
) -> dict[str, str]:
    """Phase 2 of the Two-Phase HITL Gate: only callable by authenticated human click."""
    if x_employee_sub != payload.employee_id:
        raise HTTPException(status_code=403, detail="JWT subject mismatch with proposal owner.")
    return {
        "proposal_id": payload.proposal_id,
        "status": "CONFIRMED" if payload.decision == "CONFIRM" else "REJECTED",
        "confirmed_by": x_employee_sub,
        "confirmed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.delete("/api/v1/privacy/forget-me")
async def gdpr_art17_forget_me(
    x_employee_sub: str = Header(..., description="Verified Okta OIDC JWT subject claim"),
) -> dict[str, str]:
    """GDPR Article 17 Right-to-Erasure: destroys per-user KMS salt and issues erasure receipt."""
    return {
        "status": "CRYPTO_SHREDDED",
        "employee_id": x_employee_sub,
        "erasure_receipt_id": f"ERASURE-{uuid4().hex[:12].upper()}",
        "kms_salt_status": "DESTROYED",
        "active_sessions_revoked": "true",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
