"""Isolated FastAPI Router for pod2_policy_rag — auto-mounted by app/fast_api_app.py."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/pod2_policy_rag", tags=["pod2_policy_rag"])


@router.get("/status")
async def pod_status() -> dict[str, str]:
    """Independent health check for pod2_policy_rag."""
    return {"pod": "pod2_policy_rag", "status": "READY"}
