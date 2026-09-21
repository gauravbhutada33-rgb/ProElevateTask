# AGENTS.md — Global Architecture & Execution Contract (HR Agentic Solution MVP 1)

> **MANDATORY FOR ALL JETSKI AGENTS:** Every engineer and Jetski instance working in this repository MUST read and obey these durable foundations before executing any slice in `./plans/`. Do not deviate from the locked tech stack, database schema, or pod directory boundaries.

---

## 1. Locked Technology Stack & Runtime Versions

| Layer | Technology / Package | Locked Version / Rule | Rationale & Stakeholder Safeguard |
| :--- | :--- | :--- | :--- |
| **Language & Package Manager** | Python `3.12+` managed via `uv` | `pyproject.toml` (`>=3.12`) | Deterministic dependency locking & native `google-agents-cli` compatibility. |
| **Agent Orchestration** | Google Agent Development Kit (`google-adk`) | `google-adk==1.3.0` (`LlmAgent` + `AgentTool`) | **Pattern C (`AgentTool` Explicit Invocation):** Sub-agents execute in isolated context windows and return typed JSON summaries to `root_agent` (`HRSupervisorAgent`). Never use unconstrained `transfer_to_agent` handoffs. |
| **LLM Serving & Privacy** | Vertex AI Agent Engine (`gemini-3.6-flash` & `gemini-3.6-pro`, configurable via `GEMINI_FLASH_MODEL` / `GEMINI_PRO_MODEL` up to `gemini-3.8-flash` / `gemini-3.8-pro`) | Vertex AI **Zero Data Retention (`ZDR`)** enabled (`X-Vertex-AI-Zero-Data-Retention: true`) | **Maria Santos (DPO) Safeguard:** Uses the latest Gemini 3.6/3.8 Flash & Pro models on Agent Engine with zero caching of employee prompts or HR tool responses in external provider logs. |
| **Tool Integration Protocol** | Model Context Protocol (`mcp` / `FastMCP`) | `mcp>=1.3.0` with `aiolimiter` Token-Bucket | **Alex Rivera (IT Director) Safeguard:** Enforces `50 RPS` (`100` burst) on `WorkWeek` HRIS and `25 RPS` (`50` burst) on `ServiceImmediately` IT connectors. |
| **Relational & Vector DB** | Cloud SQL `PostgreSQL 16` + `pgvector` (`HNSW`) | `sqlalchemy[asyncio]>=2.0.36`, `asyncpg`, `pgvector`, `testcontainers[postgres]` | **Alex Rivera (IT Director) Safeguard — ZERO SQLite Dialect Drift:** Local development and CI tests MUST use `testcontainers` (`pgvector/pgvector:pg16`). Using relational SQLite in local/CI tests is strictly forbidden. (Note: Read-only `SQLite-vec` is used *exclusively* as an in-memory/container circuit-breaker snapshot for Policy RAG when Cloud SQL RPC latency exceeds `400ms`). |
| **API & Streaming Runtime** | `FastAPI` + Server-Sent Events (`SSE`) | `fastapi>=0.115.0`, `sse-starlette` | Exposes ADK `/run_sse`, `/api/v1/chat/stream`, `/api/v1/hitl/confirm`, and `/api/v1/privacy/forget-me`. |
| **Guardrails & Safety** | Cloud Model Armor (`us-central1` $\rightarrow$ `us-east1` failover) + Cloud DLP + `<5ms` `google-re2` | **No In-Process ONNX Models** | **Alex Rivera Safeguard:** Keeps Cloud Run container image lean (`<250MB`) and cold-start under `1.5s` with Startup CPU Boost. |
| **Frontend UI** | `React 19` + `TypeScript 5.7` + `Vite` + `TailwindCSS` | Located in `app/frontend/` | Renders streamed SSE tokens and typed interactive cards (`<HITLConfirmationCard />`, `<CitationDrawer />`, `<SagaStatusStepper />`). |
| **Evaluation Pipeline** | `google-agents-cli` (`agents-cli eval`) | Configured in `tests/eval/eval_config.yaml` | Official Elevate Evaluator Tab 2 structure (`tests/eval/datasets/*.json` + `tests/eval/evaluation_report.md`). |

---

## 2. Global 6-Table PostgreSQL 16 Schema (`app/core/models.py`)

All 5 pods share the canonical 6-table schema defined in `app/core/models.py`. **Do NOT invent duplicate tables or modify core column names without updating `app/core/models.py`:**

1. **`user_salts`**: `(employee_id VARCHAR PK, kms_key_resource_name TEXT, user_salt BYTEA, created_at TIMESTAMPTZ, destroyed_at TIMESTAMPTZ NULL)` — Stores per-employee KMS-wrapped cryptographic salt for GDPR Art. 17 crypto-shredding (`HMAC-SHA256(employee_id, user_salt)`).
2. **`sessions`**: `(session_id UUID PK, pseudonym_hash CHAR(64) INDEX, country_code CHAR(2), role VARCHAR(32), is_manager BOOLEAN, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ)` — Stores active session state keyed by pseudonymized employee hash.
3. **`conversation_turns`**: `(turn_id UUID PK, session_id UUID FK, role VARCHAR(16), redacted_content TEXT, encrypted_pii_blob BYTEA NULL, sentiment_score FLOAT, confidence_score FLOAT, created_at TIMESTAMPTZ)` — Stores DLP-redacted transcript turns; `encrypted_pii_blob` becomes permanently unreadable upon `user_salts` deletion.
4. **`hitl_proposals`**: `(proposal_id UUID PK, session_id UUID FK, employee_id VARCHAR, tool_name VARCHAR(64), proposed_payload JSONB, idempotency_key CHAR(64) UNIQUE, status VARCHAR(24), expires_at TIMESTAMPTZ, created_at TIMESTAMPTZ)` — Enforces the 15-minute TTL two-phase Human-in-the-Loop gate (`PENDING` $\rightarrow$ `CONFIRMED` | `REJECTED` | `EXPIRED` | `QUEUED_RETRY`).
5. **`audit_trail_logs`**: `(log_id UUID PK, pseudonym_hash CHAR(64) INDEX, action_type VARCHAR(64), target_system VARCHAR(32), status VARCHAR(24), erasure_receipt_id VARCHAR(64) NULL, metadata_json JSONB, created_at TIMESTAMPTZ)` — Immutable 7-year compliance ledger (`INSERT`-only; contains zero raw PII).
6. **`hr_policy_chunks`**: `(chunk_id VARCHAR(64) PK, doc_id VARCHAR(64), section_anchor VARCHAR(64), country_code CHAR(2) INDEX, min_role VARCHAR(32) INDEX, content_text TEXT, content_tsv TSVECTOR, embedding VECTOR(768), sha256_checksum CHAR(64), updated_at TIMESTAMPTZ)` — Hybrid `pgvector` HNSW + Full-Text Search index with mandatory pre-retrieval entitlement columns (`country_code`, `min_role`).

---

## 3. Strict 5-Pod Directory Boundaries (Zero Merge Conflict Rule)

To enable 5 engineers + Jetski agents to build in parallel on separate Git branches (`feat/pod1-*` through `feat/pod5-*`), **every engineer MUST restrict code edits to their assigned vertical slice directories**:

| Pod | Engineer Assignment | Branch Name | Owned Backend Slice | Owned Frontend Slice | Owned Unit Tests & Plan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Wave 0** | Shared Foundation Spine | `main` | `app/core/`, `app/agent.py`, `app/fast_api_app.py` | `app/frontend/src/core/` | `tests/unit/test_tracer_bullet.py`, `plans/00-tracer-bullet-spine.md` |
| **Pod 1** | Engineer 1 (Security, Auth & GDPR) | `feat/pod1-security-gdpr` | `app/slices/pod1_security_privacy/` | `app/frontend/src/features/pod1_security_privacy/` | `tests/unit/test_pod1_security_gdpr.py`, `plans/01-pod1-auth-guardrails-gdpr.md` |
| **Pod 2** | Engineer 2 (Policy RAG & Citations) | `feat/pod2-policy-rag` | `app/slices/pod2_policy_rag/` | `app/frontend/src/features/pod2_policy_rag/` | `tests/unit/test_pod2_policy_rag.py`, `plans/02-pod2-policy-rag-citations.md` |
| **Pod 3** | Engineer 3 (WorkWeek Leave & HITL) | `feat/pod3-workweek-hitl` | `app/slices/pod3_workweek_leave/` | `app/frontend/src/features/pod3_workweek_leave/` | `tests/unit/test_pod3_workweek_hitl.py`, `plans/03-pod3-workweek-leave-hitl.md` |
| **Pod 4** | Engineer 4 (IT Service & 2-System Saga) | `feat/pod4-it-saga` | `app/slices/pod4_it_saga/` | `app/frontend/src/features/pod4_it_saga/` | `tests/unit/test_pod4_it_saga.py`, `plans/04-pod4-it-saga-compensation.md` |
| **Pod 5** | Engineer 5 (Escalation, Telemetry & Evals) | `feat/pod5-escalation-evals` | `app/slices/pod5_escalation_evals/` | `app/frontend/src/features/pod5_escalation_evals/` | `tests/unit/test_pod5_escalation.py`, `plans/05-pod5-escalation-and-evals.md` |

---

## 4. Non-Negotiable Security & Reliability Rules

1. **Build-Time Exclusion of Mock Auth:** `MockIdP` JWT helpers may ONLY reside in `tests/fixtures/mock_idp.py`. Production code in `app/slices/pod1_security_privacy/auth.py` validates exclusively against Okta OIDC JWKS (`OKTA_ISSUER_URI`).
2. **Synchronous `<2ms` Pre-Retrieval Entitlement Gate:** In `pod2_policy_rag`, every vector/hybrid SQL query MUST bind `WHERE country_code IN (:user_country, 'GLOBAL') AND min_role <= :user_role` *before* `ORDER BY embedding <=> :query_vec`. Post-retrieval access filtering is forbidden.
3. **Two-Phase HITL Structural Separation:** In `pod3_workweek_leave` and `pod4_it_saga`, `propose_*` tools called by the LLM may ONLY write a `PENDING` row to `hitl_proposals` and return a `proposal_id` + UI widget payload. Only the FastAPI REST endpoint `POST /api/v1/hitl/confirm` (authenticating the human click + JWT subject match) may invoke `commit_*`.
4. **Unified `<= 60 Seconds` Freshness SLA:** Both HRIS leave balance cache invalidation (`POST /api/v1/webhooks/workweek`) and HR Policy RAG chunk incremental re-indexing (`POST /api/v1/webhooks/policy-publish`) enforce a single `<= 60s` propagation SLA (`Redis TTL = 60s`).

---

## 5. Jetski Skills Available in `.gemini/skills/`

Every engineer cloning this repository has immediate access to three project-specific Jetski skills in `.gemini/skills/`:
- **`execute-vertical-slice`** (`.gemini/skills/execute-vertical-slice/SKILL.md`): Executes a `plans/0X-*.md` task file end-to-end using `RED -> GREEN -> REFACTOR -> EVAL`.
- **`adk-hitl-and-saga`** (`.gemini/skills/adk-hitl-and-saga/SKILL.md`): Provides canonical code templates for ADK Pattern C `AgentTool`, SHA-256 `hitl_proposals`, Token-Bucket throttling, and 2-System Saga compensation.
- **`elevate-eval-runner`** (`.gemini/skills/elevate-eval-runner/SKILL.md`): Runs `agents-cli eval run` against `tests/eval/eval_config.yaml` and updates `tests/eval/evaluation_report.md`.
