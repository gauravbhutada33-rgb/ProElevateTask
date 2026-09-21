"""Isolated FastAPI Router for pod5_escalation_evals — auto-mounted by app/fast_api_app.py."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/pod5_escalation_evals", tags=["pod5_escalation_evals"])


@router.get("/status")
async def pod_status() -> dict[str, str]:
    """Independent health check for pod5_escalation_evals."""
    return {"pod": "pod5_escalation_evals", "status": "READY"}
