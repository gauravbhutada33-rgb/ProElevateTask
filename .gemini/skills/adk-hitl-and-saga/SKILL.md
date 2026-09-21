---
name: adk-hitl-and-saga
description: Provides canonical implementation patterns for ADK Pattern C AgentTool wrappers, Two-Phase HITL SHA-256 proposal/commit gates, Token-Bucket API rate limiting (50 RPS / 25 RPS), and Two-System HRIS+IT Saga compensation rollback. Use when implementing Pod 3 (WorkWeek HRIS) or Pod 4 (ServiceImmediately IT Saga).
---

# ADK Pattern C (`AgentTool`), Two-Phase HITL Gate & Two-System Saga Reference

Use these exact architectural patterns to ensure zero drift between `SDD.md` and `app/`.

## 1. ADK Pattern C: Specialist Sub-Agent Wrapped as `AgentTool`

Never use unconstrained peer-to-peer `transfer_to_agent` handoffs. Wrap every pod's specialist `LlmAgent` inside an `AgentTool` so the sub-agent runs in a bounded sub-context and returns structured JSON to `HRSupervisorAgent`:

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

hris_specialist_agent = LlmAgent(
    name="hris_action_agent",
    model=settings.GEMINI_FLASH_MODEL,  # Defaults to "gemini-3.6-flash" (supports "gemini-3.8-flash")
    instruction=(
        "You are the WorkWeek HRIS Specialist Agent. "
        "You may read leave balances using `get_leave_balance`. "
        "For any state mutation (submitting or cancelling leave), you MUST ONLY call "
        "`propose_leave_request` and return the resulting `proposal_id` and `hitl_card` JSON. "
        "You can NEVER directly commit a mutation."
    ),
    tools=[get_leave_balance, propose_leave_request],
)

hris_agent_tool = AgentTool(agent=hris_specialist_agent)
```

## 2. Two-Phase HITL Proposal vs. Commit Gate (`hitl_proposals`)

1. **Phase 1 (`propose_*` — Agent Callable):**
   - Computes `idempotency_key = hashlib.sha256(f"{employee_id}:{tool_name}:{canonical_json}".encode()).hexdigest()`.
   - Inserts row into `hitl_proposals` (`status="PENDING"`, `expires_at=now() + timedelta(minutes=15)`).
   - Emits SSE event `{ "type": "hitl_card", "proposal_id": str(proposal_id), ... }`.
2. **Phase 2 (`POST /api/v1/hitl/confirm` — Human REST Endpoint Only):**
   - Verifies the caller's Okta JWT `sub == proposal.employee_id`.
   - Verifies `proposal.status == "PENDING"` and `proposal.expires_at > now()`.
   - Executes `commit_leave_request` against `WorkWeek` using the `50 RPS` (`100` burst) `AsyncLimiter`.
   - On HTTP `429` or `5xx`, respects `Retry-After`, transitions status to `QUEUED_RETRY`, and enqueues payload into Google Cloud Tasks (`ww-it-mutation-retry-queue`).

## 3. Two-System Saga Coordinator (`WorkWeek` + `ServiceImmediately`)

When executing a workflow that spans both `WorkWeek` (Step 1) and `ServiceImmediately` (Step 2):
1. Record Saga start in `audit_trail_logs` (`status="SAGA_STARTED"`).
2. Execute Step 1 (`WorkWeek` mutation) $\rightarrow$ transition state to `HR_COMMITTED`.
3. Execute Step 2 (`ServiceImmediately` ticket creation using `AsyncLimiter(25, 1.0)`).
4. If Step 2 raises `TimeoutError` or returns `5xx` after retry budget:
   - Immediately invoke compensating action `cancel_leave_request(hr_transaction_id)` on `WorkWeek`.
   - Transition state to `ROLLBACK_EXECUTED` in `audit_trail_logs` and notify user via `<SagaStatusStepper />`.
