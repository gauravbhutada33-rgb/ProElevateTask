# Enterprise HR Agentic Solution (MVP 1)

Official repository for the **Enterprise HR Agentic Solution (MVP 1)** built on **Google Agent Development Kit (`google-adk`)** and **Vertex AI Agent Engine (`gemini-3.6-flash` & `gemini-3.6-pro`)**, structured to score near-perfect across all three tabs of the **Elevate Evaluator** (`Software Design`, `Agent Evaluation`, and `Codebase Readiness`).

---

## 1. Prescribed Repository Structure (`agents-cli` Compliant)

```text
hr-agentic-solution/
├── app/                                 # Core ADK Pattern C Supervisor + 5 Vertical Slices
│   ├── agent.py                         # Root `root_agent` (HRSupervisorAgent on gemini-3.6-pro)
│   ├── fast_api_app.py                  # FastAPI SSE, HITL Confirmation & GDPR Art. 17 endpoints
│   ├── core/                            # Global settings (`config.py`) & 6-table PostgreSQL 16 DDL (`models.py`)
│   ├── slices/                          # 5 Isolated Backend Vertical Slices (1 per Engineer Pod)
│   │   ├── pod1_security_privacy/       # Pod 1: Okta JWT, Speculative Model Armor/DLP, GDPR Art. 17
│   │   ├── pod2_policy_rag/             # Pod 2: <2ms Entitlement Gate, Hybrid pgvector/SQLite-vec RAG
│   │   ├── pod3_workweek_leave/         # Pod 3: WorkWeek MCP (50 RPS), Two-Phase HITL Gate, Cloud Tasks
│   │   ├── pod4_it_saga/                # Pod 4: ServiceImmediately MCP (25 RPS), Two-System Saga Rollback
│   │   └── pod5_escalation_evals/       # Pod 5: Sentiment Escalation (< -0.4), Warm Handoff, FinOps & Evals
│   └── frontend/                        # React 19 + TypeScript SSE Chat & Interactive Widget UI
├── tests/
│   ├── eval/                            # [Elevate Evaluator Tab 2] Official `agents-cli` Evaluation Suite
│   │   ├── datasets/
│   │   │   ├── eval-single-turn.json    # Single-turn Policy RAG grounding, Entitlements & Safety cases
│   │   │   └── eval-multi-turn.json     # Multi-turn HITL Approval, 2-System Saga Rollback & Warm Handoff
│   │   ├── eval_config.yaml             # Metrics (`gemini-3.6-pro` judge) & custom compliance rubrics
│   │   └── evaluation_report.md         # Evaluation methodology, benchmarks & Quality Flywheel guide
│   └── unit/                            # Deterministic pytest unit & Testcontainers PostgreSQL 16 tests
├── .gemini/skills/                      # Git-tracked Jetski Skills auto-loaded for all 5 team members
│   ├── execute-vertical-slice/SKILL.md
│   ├── adk-hitl-and-saga/SKILL.md
│   └── elevate-eval-runner/SKILL.md
├── plans/                               # Dependency-ordered Vertical Slice Task Files (Wave 0 + Pods 1–5)
│   ├── 00-tracer-bullet-spine.md
│   ├── 01-pod1-auth-guardrails-gdpr.md
│   ├── 02-pod2-policy-rag-citations.md
│   ├── 03-pod3-workweek-leave-hitl.md
│   ├── 04-pod4-it-saga-compensation.md
│   └── 05-pod5-escalation-and-evals.md
├── agents-cli-manifest.yaml             # Official `agents-cli` manifest
├── pyproject.toml                       # Locked Python 3.12+ dependencies & pytest/ruff/mypy config
├── AGENTS.md                            # Durable Global Rules & 6-Table Schema Contract for Jetski
└── SDD.md                               # Canonical Enterprise Agentic Solution Design Document (v1.3)
```

---

## 2. Quickstart for the 5-Engineer Jetski Team

### Step 1: Clone & Verify Wave 0 Spine
```bash
git clone https://github.com/gururay001/hr-agentic-solution.git
cd hr-agentic-solution
uv run --extra dev pytest tests/unit/test_tracer_bullet.py -v
```

### Step 2: Pick Your Assigned Pod Plan & Branch
Each engineer works on their isolated vertical slice branch using Jetski:

| Engineer | Pod Branch | Jetski Prompt to Start Implementation |
| :--- | :--- | :--- |
| **Engineer 1** | `feat/pod1-security-gdpr` | *"Read `@AGENTS.md` and execute `@plans/01-pod1-auth-guardrails-gdpr.md` using `/execute-vertical-slice`."* |
| **Engineer 2** | `feat/pod2-policy-rag` | *"Read `@AGENTS.md` and execute `@plans/02-pod2-policy-rag-citations.md` using `/execute-vertical-slice`."* |
| **Engineer 3** | `feat/pod3-workweek-hitl` | *"Read `@AGENTS.md` and execute `@plans/03-pod3-workweek-leave-hitl.md` using `/execute-vertical-slice`."* |
| **Engineer 4** | `feat/pod4-it-saga` | *"Read `@AGENTS.md` and execute `@plans/04-pod4-it-saga-compensation.md` using `/execute-vertical-slice`."* |
| **Engineer 5** | `feat/pod5-escalation-evals` | *"Read `@AGENTS.md` and execute `@plans/05-pod5-escalation-and-evals.md` using `/execute-vertical-slice`."* |

### Step 3: Run `agents-cli` Evaluation Suite
```bash
agents-cli eval run --config tests/eval/eval_config.yaml
```
