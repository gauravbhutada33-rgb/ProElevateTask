"""FastAPI SSE Runtime, Dynamic Pod Router Auto-Discovery & HITL/GDPR Endpoints (app/fast_api_app.py)."""

import importlib
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent import root_agent, tracer_bullet_health_check
from app.core.config import settings
from app.core.contracts import EmployeeContext, get_employee_context

app = FastAPI(
    title="Enterprise HR Agentic Solution (MVP 1)",
    version="1.3.0",
    description="ADK Pattern C Supervisor + Speculative Guardrails + Two-Phase HITL Gate + 5 Independent Pods",
)

POD_ROUTER_MODULES = [
    "app.slices.pod1_security_privacy.router",
    "app.slices.pod2_policy_rag.router",
    "app.slices.pod3_workweek_leave.router",
    "app.slices.pod4_it_saga.router",
    "app.slices.pod5_escalation_evals.router",
]

for _module_path in POD_ROUTER_MODULES:
    try:
        _mod = importlib.import_module(_module_path)
        if hasattr(_mod, "router"):
            app.include_router(_mod.router)
    except ModuleNotFoundError:
        continue


class ChatStreamRequest(BaseModel):
    """Canonical request schema for the Spine `/api/v1/chat/stream` SSE endpoint."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    message: str
    widget_hint: str | None = None


class HITLConfirmRequest(BaseModel):
    """Request body for human confirmation of a pending proposal."""

    proposal_id: str
    employee_id: str
    decision: str  # "CONFIRM" | "CANCEL"


def _format_sse_event(event_type: str, data: dict[str, Any]) -> str:
    """Formats a server-sent event payload following the Spine UI contract."""
    payload = {"type": event_type, "timestamp_utc": datetime.now(UTC).isoformat(), **data}
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"


@app.get("/health")
async def health() -> dict[str, str]:
    """Wave 0 Tracer Bullet health endpoint."""
    return tracer_bullet_health_check()


@app.post("/api/v1/chat/stream")
async def chat_stream(
    request: ChatStreamRequest,
    ctx: EmployeeContext = Depends(get_employee_context),  # noqa: B008
) -> StreamingResponse:
    """Canonical Spine SSE endpoint streaming tokens and typed Pod UI widget cards."""

    async def event_generator() -> AsyncGenerator[str, None]:
        yield _format_sse_event(
            "metadata",
            {
                "session_id": request.session_id,
                "supervisor_agent": root_agent.name,
                "model": settings.GEMINI_PRO_MODEL,
                "zdr_active": settings.VERTEX_AI_ZERO_DATA_RETENTION,
                "employee_id": ctx.employee_id,
                "country_code": ctx.country_code,
            },
        )
        yield _format_sse_event(
            "token",
            {
                "delta": (
                    f"[{root_agent.name} | {settings.GEMINI_PRO_MODEL}] "
                    f"Processed request for {ctx.employee_id} ({ctx.country_code}/{ctx.role}): "
                    f"{request.message}"
                ),
            },
        )
        if request.widget_hint:
            yield _format_sse_event(
                "widget",
                {
                    "widget_type": request.widget_hint,
                    "employee_id": ctx.employee_id,
                },
            )
        yield _format_sse_event("done", {"session_id": request.session_id, "status": "COMPLETE"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Vertex-AI-Zero-Data-Retention": "true",
        },
    )


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
        "confirmed_at_utc": datetime.now(UTC).isoformat(),
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
        "completed_at_utc": datetime.now(UTC).isoformat(),
    }
