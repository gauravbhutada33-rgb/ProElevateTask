"""Isolated Sub-Agent for pod3_workweek_leave — auto-discovered by app/agent.py.

Pre-wired to both the Plan 03 Two-Phase HITL tools (`get_leave_balance`, `propose_leave_request`)
and the live WorkWeek MCP Server (`https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/`).
"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.core.config import settings
from app.core.mcp_client import (
    workweek_get_current_employee_id,
    workweek_get_employee_balances,
    workweek_get_leave_requests,
    workweek_get_personal_info,
    workweek_propose_time_off,
    workweek_propose_update_personal_info,
)
from app.slices.pod3_workweek_leave.mcp_tools import (
    get_leave_balance,
    propose_leave_request,
)

specialist_agent = LlmAgent(
    name="hris_action_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Pod 3: WorkWeek HRIS MCP (50 RPS) & Two-Phase HITL Gate for employee EMP-824.",
    instruction=(
        "You are `hris_action_agent` (Pod 3) connected to WorkWeek HRIS MCP (50 RPS). "
        "You may read leave balances and employee info using `get_leave_balance`, "
        "`workweek_get_current_employee_id`, `workweek_get_employee_balances`, "
        "`workweek_get_personal_info`, and `workweek_get_leave_requests`. "
        "For any state mutation (submitting PTO/Vacation/Sick leave or contact updates), "
        "you MUST ONLY call `propose_leave_request`, `workweek_propose_time_off`, or "
        "`workweek_propose_update_personal_info` to emit a 15-minute TTL `proposal_id` and "
        "`hitl_card` JSON, and wait for human confirmation via `/api/v1/hitl/confirm`. "
        "You can NEVER directly commit a mutation."
    ),
    tools=[
        get_leave_balance,
        propose_leave_request,
        workweek_get_current_employee_id,
        workweek_get_employee_balances,
        workweek_get_personal_info,
        workweek_get_leave_requests,
        workweek_propose_time_off,
        workweek_propose_update_personal_info,
    ],
)

HRISActionAgent = specialist_agent
hris_specialist_agent = specialist_agent
hris_agent_tool = AgentTool(agent=specialist_agent)
pod3_agent_tool = hris_agent_tool


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return hris_agent_tool


__all__ = [
    "HRISActionAgent",
    "get_agent_tool",
    "hris_agent_tool",
    "hris_specialist_agent",
    "pod3_agent_tool",
    "specialist_agent",
]
