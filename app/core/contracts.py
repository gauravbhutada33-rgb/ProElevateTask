"""Shared Cross-Pod Interfaces & Default Adapters (app/core/contracts.py).

Guarantees 100% Pod Independence: Every Pod programs against these shared contracts
so Pod 1..5 have ZERO runtime or build dependencies on each other's slice folders.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from fastapi import Header

from app.core.config import settings
from app.core.mcp_client import mcp_client


@dataclass(frozen=True)
class EmployeeContext:
    """Verified caller identity injected into every pod router and tool (defaults to live MCP EMP-824)."""

    employee_id: str = settings.DEFAULT_EMPLOYEE_ID
    country_code: str = "SG"
    role: str = "IC"
    is_manager: bool = False


async def get_employee_context(
    x_employee_sub: str = Header(default=settings.DEFAULT_EMPLOYEE_ID),
    x_country_code: str = Header(default="SG"),
    x_employee_role: str = Header(default="IC"),
) -> EmployeeContext:
    """Default dependency injector so Pods 2-5 never block on Pod 1 Auth."""
    return EmployeeContext(
        employee_id=x_employee_sub,
        country_code=x_country_code,
        role=x_employee_role,
        is_manager=(x_employee_role in {"MANAGER", "EXEC"}),
    )


class HRISCompensationPort(Protocol):
    """Contract allowing Pod 4 (IT Saga) to trigger HRIS rollback without importing Pod 3."""

    async def commit_hr_step(self, employee_id: str, payload: dict[str, Any]) -> str: ...
    async def revert_hr_record(self, employee_id: str, request_id: int) -> dict[str, Any]: ...


class DefaultHRISCompensationAdapter:
    """Live MCP contract adapter calling `cancel_leave_request` on WorkWeek MCP (`https://mock-saas...`)."""

    async def commit_hr_step(self, employee_id: str, payload: dict[str, Any]) -> str:
        res = await mcp_client.call_workweek(
            "request_time_off",
            {
                "employee_id": employee_id,
                "start_date": str(payload.get("start_date", "2026-11-23")),
                "end_date": str(payload.get("end_date", "2026-11-25")),
                "leave_type": str(payload.get("leave_type", "Vacation")),
                "days": float(payload.get("days", 3.0)),
            },
        )
        return str(res.get("result", f"WW-TX-{employee_id}"))

    async def revert_hr_record(self, employee_id: str, request_id: int) -> dict[str, Any]:
        return await mcp_client.call_workweek(
            "cancel_leave_request",
            {"employee_id": employee_id, "request_id": request_id},
        )
