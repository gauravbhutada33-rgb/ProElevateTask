"""Root ADK Supervisor Agent with Dynamic Pod Auto-Discovery — app/agent.py.

No engineer ever needs to edit `app/agent.py`—it automatically discovers `get_agent_tool()`
from each pod's isolated `app/slices/pod*/sub_agent.py` module.
"""

import importlib
from typing import Any

from google.adk.agents import LlmAgent

from app.core.config import settings

POD_SLICE_MODULES = [
    "app.slices.pod1_security_privacy.sub_agent",
    "app.slices.pod2_policy_rag.sub_agent",
    "app.slices.pod3_workweek_leave.sub_agent",
    "app.slices.pod4_it_saga.sub_agent",
    "app.slices.pod5_escalation_evals.sub_agent",
]


def tracer_bullet_health_check(employee_id: str = "EMP-1042", country_code: str = "US") -> dict[str, str]:
    """Wave 0 Tracer Bullet tool verifying supervisor routing, model tier, and ZDR config."""
    return {
        "status": "HEALTHY",
        "employee_id": employee_id,
        "country_code": country_code,
        "flash_model": settings.GEMINI_FLASH_MODEL,
        "pro_model": settings.GEMINI_PRO_MODEL,
        "zdr_enabled": str(settings.VERTEX_AI_ZERO_DATA_RETENTION),
    }


def _discover_pod_agent_tools() -> list[Any]:
    """Dynamically loads `get_agent_tool()` from each pod slice without merge conflicts."""
    tools: list[Any] = [tracer_bullet_health_check]
    for module_path in POD_SLICE_MODULES:
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, "get_agent_tool"):
                tools.append(mod.get_agent_tool())
        except ModuleNotFoundError:
            continue
    return tools


root_agent = LlmAgent(
    name="hr_supervisor_agent",
    model=settings.GEMINI_PRO_MODEL,
    description="Enterprise HR Agentic Supervisor (Pattern C AgentTool Router) on Vertex AI Agent Engine.",
    instruction=(
        "You are the Enterprise HR Supervisor Agent powered by Gemini 3.6 Pro / Flash on Vertex AI "
        "Agent Engine with Zero Data Retention (ZDR). Route security/privacy inquiries to "
        "`security_privacy_agent`, policy inquiries to `policy_rag_agent`, WorkWeek leave inquiries "
        "to `hris_action_agent`, IT/Cross-domain sagas to `it_service_agent`, and distressed employee "
        "escalations to `escalation_agent`. Never commit any write action without a human-confirmed `proposal_id`."
    ),
    tools=_discover_pod_agent_tools(),
)
