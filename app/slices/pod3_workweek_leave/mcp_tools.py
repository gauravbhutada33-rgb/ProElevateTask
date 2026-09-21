"""WorkWeek HRIS MCP Tools for ADK Pattern C Specialist Sub-Agent (app/slices/pod3_workweek_leave/mcp_tools.py).

STRICT GOV-03 FIREWALL: `commit_leave_request` / `commit_leave_to_workweek` is NEVER exposed here.
Only `get_leave_balance` and `propose_leave_request` are callable by the LLM.
"""

from typing import Any

from mcp.server.mcpserver import MCPServer as FastMCP

from app.slices.pod3_workweek_leave.hitl_service import (
    propose_leave_request as _propose_leave_request_impl,
)
from app.slices.pod3_workweek_leave.workweek_client import (
    get_leave_balance as _get_leave_balance_impl,
)

mcp_server = FastMCP("workweek-hris-mcp")


@mcp_server.tool(name="get_leave_balance")
async def get_leave_balance(employee_id: str = "EMP-1042") -> dict[str, Any]:
    """Reads an employee's available PTO, parental leave, and sick leave balances from WorkWeek HRIS."""
    balance = await _get_leave_balance_impl(employee_id=employee_id)
    return balance.model_dump()


@mcp_server.tool(name="propose_leave_request")
async def propose_leave_request(
    employee_id: str = "EMP-1042",
    start_date: str = "2026-11-23",
    end_date: str = "2026-11-25",
    days: float = 3.0,
    leave_type: str = "PTO",
) -> dict[str, Any]:
    """Creates a PENDING Two-Phase HITL leave request proposal (15-min TTL) and returns a hitl_card payload."""
    return await _propose_leave_request_impl(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        leave_type=leave_type,
    )


__all__ = ["get_leave_balance", "mcp_server", "propose_leave_request"]
