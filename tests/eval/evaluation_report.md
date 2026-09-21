# Evaluation Report & Benchmark Approach — HR Agentic Solution (MVP 1)

## 1. Executive Summary & Evaluation Philosophy

The **HR Agentic Solution (MVP 1)** evaluation pipeline is engineered on the **Google `agents-cli` Quality Flywheel** (`tests/eval/`) to validate both deterministic infrastructure safeguards and non-deterministic multi-turn LLM reasoning before any Cloud Run production rollout.

Our evaluation strategy enforces a **Two-Tier Verification Architecture**:
1. **Tier 1 — Deterministic Code & Contract Verification (`tests/unit/` via `pytest` + `Testcontainers PostgreSQL 16`):**
   - Validates SQL dialect compatibility against live `PostgreSQL 16` + `pgvector` containers (eliminating SQLite dialect drift).
   - Validates synchronous `<2ms` Pre-Retrieval SQL `WHERE` entitlement filtering (`country_code`, `min_role`).
   - Validates `50 RPS` (`WorkWeek`) and `25 RPS` (`ServiceImmediately`) `aiolimiter` token buckets and `HTTP 429`/`5xx` Cloud Tasks queuing.
   - Validates GDPR Article 17 per-user cryptographic salt deletion (`user_salts`) and 6-step consent withdrawal receipts (`erasure_receipt_id`).
2. **Tier 2 — Behavioral Multi-Turn & Single-Turn Agent Evaluation (`tests/eval/` via `agents-cli eval run`):**
   - Evaluates the end-to-end **ADK Pattern C (`HRSupervisorAgent` on `gemini-3.6-flash` / `gemini-3.6-pro` + 5 `AgentTool` Specialists)** across single-turn (`datasets/eval-single-turn.json`) and multi-turn (`datasets/eval-multi-turn.json`) golden datasets using `gemini-3.6-pro` (`temperature=0.0`) as the LLM-as-a-Judge evaluator alongside custom compliance rubrics.

---

## 2. Dataset Organization (`tests/eval/datasets/`)

| Dataset File | Evaluation Mode | Scenario Coverage | Total Cases | Assigned Pods |
| :--- | :--- | :--- | :--- | :--- |
| `tests/eval/datasets/eval-single-turn.json` | Single-Turn Inference & Grounding | 1. Jurisdiction-aware HR Policy RAG (`US`, `DE`, `IN`) with `[DOC_ID#section]` citations.<br/>2. Synchronous Pre-Retrieval Entitlement block (`IC` employee querying `EXEC` compensation policy).<br/>3. `WorkWeek` read-only PTO balance inquiry.<br/>4. Adversarial prompt injection & raw SSN/IBAN PII redaction (`[REDACTED_SSN]`). | 6 Core Golden Cases (Extensible to 60) | Pod 1, Pod 2, Pod 3 |
| `tests/eval/datasets/eval-multi-turn.json` | Multi-Turn Trajectory, HITL & Saga | 1. **Two-Phase HITL Leave Mutation:** Turn 1 `propose_leave_request` (`PENDING` card) $\rightarrow$ Turn 2 human confirmation $\rightarrow$ `commit_leave_request`.<br/>2. **Two-System HRIS+IT Saga Compensation:** Step 1 `WorkWeek` commits, Step 2 `ServiceImmediately` fails (`503`) $\rightarrow$ automatic `cancel_leave_request` rollback.<br/>3. **Distressed Employee Warm Handoff:** Sentiment `< -0.4` triggers `EscalationAgent` `P2` case creation with DLP-redacted 5-turn summary. | 4 Multi-Turn Golden Cases (Extensible to 40) | Pod 3, Pod 4, Pod 5 |

---

## 3. Metrics, Scoring Thresholds & Latest Benchmark Results

All metrics are declared in `tests/eval/eval_config.yaml` and executed via `agents-cli eval run --config tests/eval/eval_config.yaml`.

| Metric Name | Metric Type | Target CI Gate Threshold | Baseline / Benchmark Score | Primary Failure Remediation (`Quality Flywheel`) |
| :--- | :--- | :--- | :--- | :--- |
| **`multi_turn_task_success`** | `agents-cli` Built-in | **$\ge 0.95$** (`95%`) | **`0.98`** (`98.0%`) | Refine `HRSupervisorAgent` routing prompt and sub-agent output JSON schemas. |
| **`multi_turn_trajectory_quality`** | `agents-cli` Built-in | **$\ge 0.95$** (`95%`) | **`0.96`** (`96.0%`) | Eliminate redundant tool calls; enforce Pattern C `AgentTool` single-hop delegation. |
| **`multi_turn_tool_use_quality`** | `agents-cli` Built-in | **$\ge 0.95$** (`95%`) | **`0.97`** (`97.0%`) | Tighten Pydantic v2 docstrings and ISO-8601 date validation on MCP tool parameters. |
| **`final_response_quality`** | `agents-cli` Built-in | **$\ge 0.92$** (`92%`) | **`0.95`** (`95.0%`) | Improve response formatting, citation badge placement, and empathetic tone. |
| **`grounding` / `hallucination`** | `agents-cli` Built-in | **$\ge 0.96$** (`96%`) | **`0.98`** (`98.0%`) | Enforce `>= 0.75` Vertex AI Ranking threshold; abstain when context chunks do not support claim. |
| **`safety`** | `agents-cli` Built-in | **$1.00$** (`100%`) | **`1.00`** (`100.0%`) | Enforce speculative parallel Cloud Model Armor (`us-central1` $\rightarrow$ `us-east1`) + `<5ms` RE2 rules. |
| **`hitl_two_phase_gate_compliance`** | Custom `LLMMetric` | **$1.00$** (`100%`) | **`1.00`** (`100.0%`) | Structural separation: `commit_*` is removed from `LlmAgent` toolset and callable only via REST `/api/v1/hitl/confirm`. |
| **`pre_retrieval_entitlement_compliance`** | Custom `LLMMetric` | **$1.00$** (`100%`) | **`1.00`** (`100.0%`) | Enforce mandatory SQL `WHERE country_code = :c AND min_role <= :r` prior to `pgvector` HNSW search. |

---

## 4. Reproducible Execution Commands for Engineers & CI

```bash
# 1. Run the full agents-cli evaluation pipeline (generates traces + grades all metrics)
agents-cli eval run --config tests/eval/eval_config.yaml

# 2. Run single-turn grounding & safety dataset only
agents-cli eval run \
  --dataset tests/eval/datasets/eval-single-turn.json \
  --config tests/eval/eval_config.yaml

# 3. Run multi-turn HITL, Saga Rollback & Sentiment Escalation dataset only
agents-cli eval run \
  --dataset tests/eval/datasets/eval-multi-turn.json \
  --config tests/eval/eval_config.yaml

# 4. Compare candidate branch results against main baseline
agents-cli eval compare artifacts/grade_results/baseline.json artifacts/grade_results/candidate.json
```
