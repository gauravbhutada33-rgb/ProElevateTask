"""Isolated Sub-Agent for pod5_escalation_evals — auto-discovered by app/agent.py."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.core.config import settings

specialist_agent = LlmAgent(
    name="escalation_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Pod 5: Sentiment Warm Handoff, FinOps Telemetry & Golden-100 Eval Gate",
    instruction="You are escalation_agent (Pod 5: Sentiment Warm Handoff, FinOps Telemetry & Golden-100 Eval Gate). Operate strictly within your vertical slice contract.",
)


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return AgentTool(agent=specialist_agent)
