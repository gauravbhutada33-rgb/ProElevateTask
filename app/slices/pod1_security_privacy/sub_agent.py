"""Isolated Sub-Agent for pod1_security_privacy — auto-discovered by app/agent.py."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.core.config import settings

specialist_agent = LlmAgent(
    name="security_privacy_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Pod 1: Zero-Trust Auth, Speculative Guardrails & GDPR Art. 17",
    instruction="You are security_privacy_agent (Pod 1: Zero-Trust Auth, Speculative Guardrails & GDPR Art. 17). Operate strictly within your vertical slice contract.",
)


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return AgentTool(agent=specialist_agent)
