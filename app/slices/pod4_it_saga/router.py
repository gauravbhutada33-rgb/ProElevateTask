"""Isolated FastAPI Router for pod4_it_saga — auto-mounted by app/fast_api_app.py."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/pod4_it_saga", tags=["pod4_it_saga"])


@router.get("/status")
async def pod_status() -> dict[str, str]:
    """Independent health check for pod4_it_saga."""
    return {"pod": "pod4_it_saga", "status": "READY"}
