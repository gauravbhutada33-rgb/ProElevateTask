"""Isolated Sub-Agent for pod2_policy_rag — auto-discovered by app/agent.py."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.core.config import settings

specialist_agent = LlmAgent(
    name="policy_rag_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Pod 2: <2ms Pre-Retrieval Entitlement Gate & Hybrid Policy RAG",
    instruction="You are policy_rag_agent (Pod 2: <2ms Pre-Retrieval Entitlement Gate & Hybrid Policy RAG). Operate strictly within your vertical slice contract.",
)


def get_agent_tool() -> AgentTool:
    """Returns the AgentTool wrapper for automatic registration in HRSupervisorAgent."""
    return AgentTool(agent=specialist_agent)
