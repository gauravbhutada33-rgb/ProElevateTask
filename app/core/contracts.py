"""Shared Cross-Pod Interfaces & Default Adapters (app/core/contracts.py).

Guarantees 100% Pod Independence: Every Pod programs against these shared contracts
so Pod 1..5 have ZERO runtime or build dependencies on each other's slice folders.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from fastapi import Header


@dataclass(frozen=True)
class EmployeeContext:
    """Verified caller identity injected into every pod router and tool."""

    employee_id: str = "EMP-1042"
    country_code: str = "US"
    role: str = "IC"
    is_manager: bool = False


async def get_employee_context(
    x_employee_sub: str = Header(default="EMP-1042"),
    x_country_code: str = Header(default="US"),
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
    async def revert_hr_record(self, hr_transaction_id: str) -> bool: ...


class DefaultHRISCompensationAdapter:
    """Deterministic contract adapter used by Pod 4 when Pod 3 is developed in parallel."""

    async def commit_hr_step(self, employee_id: str, payload: dict[str, Any]) -> str:
        return f"WW-TX-{employee_id}"

    async def revert_hr_record(self, hr_transaction_id: str) -> bool:
        return True
