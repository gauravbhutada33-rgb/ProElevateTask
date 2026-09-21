"""Isolated Sub-Agent for pod3_workweek_leave — auto-discovered by app/agent.py."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.core.config import settings

specialist_agent = LlmAgent(
    name="hris_action_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Pod 3: WorkWeek HRIS MCP (50 RPS) & Two-Phase HITL Gate",
    instruction="You are hris_action_agent (Pod 3: WorkWeek HRIS MCP (50 RPS) & Two-Phase HITL Gate). Operate strictly within your vertical slice contract.",
)


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return AgentTool(agent=specialist_agent)
