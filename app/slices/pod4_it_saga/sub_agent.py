"""Isolated Sub-Agent for pod4_it_saga — auto-discovered by app/agent.py."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from app.core.config import settings

specialist_agent = LlmAgent(
    name="it_service_agent",
    model=settings.GEMINI_PRO_MODEL,
    description="Pod 4: ServiceImmediately IT MCP (25 RPS) & Two-System Saga Rollback",
    instruction="You are it_service_agent (Pod 4: ServiceImmediately IT MCP (25 RPS) & Two-System Saga Rollback). Operate strictly within your vertical slice contract.",
)


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return AgentTool(agent=specialist_agent)
