"""Isolated Sub-Agent for pod3_workweek_leave — auto-discovered by app/agent.py.

Pre-wired to the live WorkWeek MCP Server (`https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/`).
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

specialist_agent = LlmAgent(
    name="hris_action_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Pod 3: WorkWeek HRIS MCP (50 RPS) & Two-Phase HITL Gate for employee EMP-824.",
    instruction=(
        "You are `hris_action_agent` (Pod 3) connected to the live WorkWeek MCP Server "
        "(`https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/`) for authenticated "
        "employee `EMP-824`. You may call `workweek_get_current_employee_id`, "
        "`workweek_get_employee_balances`, `workweek_get_personal_info`, and "
        "`workweek_get_leave_requests` directly. For any leave request (`Vacation` or `Sick`) "
        "or contact info update, you MUST ONLY call `workweek_propose_time_off` or "
        "`workweek_propose_update_personal_info` to emit a 15-minute TTL `proposal_id` and wait "
        "for human confirmation via `/api/v1/hitl/confirm`."
    ),
    tools=[
        workweek_get_current_employee_id,
        workweek_get_employee_balances,
        workweek_get_personal_info,
        workweek_get_leave_requests,
        workweek_propose_time_off,
        workweek_propose_update_personal_info,
    ],
)


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return AgentTool(agent=specialist_agent)
