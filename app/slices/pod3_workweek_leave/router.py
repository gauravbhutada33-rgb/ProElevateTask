"""Isolated FastAPI Router for pod3_workweek_leave — auto-mounted by app/fast_api_app.py."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/pod3_workweek_leave", tags=["pod3_workweek_leave"])


@router.get("/status")
async def pod_status() -> dict[str, str]:
    """Independent health check for pod3_workweek_leave."""
    return {"pod": "pod3_workweek_leave", "status": "READY"}
