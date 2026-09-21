"""Root ADK Supervisor Agent (Pattern C AgentTool Orchestrator) — app/agent.py."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from app.core.config import settings


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


policy_rag_specialist = LlmAgent(
    name="policy_rag_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Answers jurisdiction-specific HR policy questions with pre-retrieval entitlement filtering and inline [DOC_ID#section] citations.",
    instruction=(
        "You are the PolicyRAGAgent (Pod 2). Enforce synchronous <2ms pre-retrieval entitlement "
        "checks on `country_code` and `role` prior to similarity search. Always cite exact "
        "`[DOC_ID#section]` anchors and refuse access to restricted Executive (`EXEC`) policies."
    ),
)

hris_action_specialist = LlmAgent(
    name="hris_action_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Reads WorkWeek PTO balances and proposes leave mutations via the Two-Phase HITL Gate (`hitl_proposals`).",
    instruction=(
        "You are the HRISActionAgent (Pod 3). You may read balances directly, but for any leave "
        "submission or modification you MUST ONLY call `propose_leave_request` (creating a 15-min "
        "TTL `proposal_id`) and pause for human confirmation via `/api/v1/hitl/confirm`."
    ),
)

it_service_specialist = LlmAgent(
    name="it_service_agent",
    model=settings.GEMINI_PRO_MODEL,
    description="Coordinates ServiceImmediately IT tickets and Two-System (WorkWeek + ServiceImmediately) Saga rollbacks.",
    instruction=(
        "You are the ITServiceAgent & Saga Coordinator (Pod 4). When executing a two-system "
        "workflow across WorkWeek and ServiceImmediately, automatically trigger compensating "
        "`revert_hr_record` / `cancel_leave_request` rollback (`ROLLBACK_EXECUTED`) if Step 2 fails."
    ),
)

escalation_specialist = LlmAgent(
    name="escalation_agent",
    model=settings.GEMINI_FLASH_MODEL,
    description="Handles distressed employee warm handoffs (sentiment < -0.4 or confidence < 0.75) by creating P2 ServiceImmediately HR cases.",
    instruction=(
        "You are the EscalationAgent (Pod 5). When employee sentiment is below -0.4 or policy "
        "confidence is below 0.75, bundle a DLP-redacted 5-turn summary and open a Priority P2 "
        "ServiceImmediately HR Case (`SI-HR-*`)."
    ),
)

root_agent = LlmAgent(
    name="hr_supervisor_agent",
    model=settings.GEMINI_PRO_MODEL,
    description="Enterprise HR Agentic Supervisor (Pattern C AgentTool Router) on Vertex AI Agent Engine.",
    instruction=(
        "You are the Enterprise HR Supervisor Agent powered by Gemini 3.6 Pro / Flash on Vertex AI "
        "Agent Engine with Zero Data Retention (ZDR). Route policy inquiries to `policy_rag_agent`, "
        "WorkWeek leave inquiries/proposals to `hris_action_agent`, IT/Cross-domain sagas to "
        "`it_service_agent`, and distressed employee escalations to `escalation_agent`. "
        "Never commit any HRIS or IT write action without an explicit human-confirmed `proposal_id`."
    ),
    tools=[
        tracer_bullet_health_check,
        AgentTool(agent=policy_rag_specialist),
        AgentTool(agent=hris_action_specialist),
        AgentTool(agent=it_service_specialist),
        AgentTool(agent=escalation_specialist),
    ],
)
