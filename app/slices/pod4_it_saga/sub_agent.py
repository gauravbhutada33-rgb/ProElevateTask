"""Isolated Sub-Agent for pod4_it_saga — auto-discovered by app/agent.py.

Pre-wired to the live ServiceImmediately MCP Server (`https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/`).
"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.core.config import settings
from app.core.mcp_client import (
    service_immediately_list_tickets,
    service_immediately_propose_ticket,
)

specialist_agent = LlmAgent(
    name="it_service_agent",
    model=settings.GEMINI_PRO_MODEL,
    description="Pod 4: ServiceImmediately IT MCP (25 RPS) & Two-System Saga Rollback for employee EMP-824.",
    instruction=(
        "You are `it_service_agent` (Pod 4) connected to the live ServiceImmediately MCP Server "
        "(`https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/`) for "
        "authenticated employee `EMP-824`. Use `service_immediately_list_tickets` to inspect "
        "existing incidents (e.g., `INC0004773`) and `service_immediately_propose_ticket` to "
        "stage new IT incidents behind the Two-Phase HITL Gate."
    ),
    tools=[
        service_immediately_list_tickets,
        service_immediately_propose_ticket,
    ],
)


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return AgentTool(agent=specialist_agent)
