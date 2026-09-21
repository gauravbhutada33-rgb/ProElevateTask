---
name: execute-vertical-slice
description: Executes a dependency-ordered vertical slice task file from ./plans/ (00 through 05) in the hr-agentic-solution repository using RED-GREEN-REFACTOR and agents-cli evaluation checkpoints. Use when an engineer asks Jetski to implement their assigned Pod slice (e.g. Pod 1 through Pod 5).
---

# Execute Vertical Slice (`./plans/0X-*.md`)

Use this skill whenever executing a vertical slice from `./plans/` for any of the 5 engineering pods (`Pod 1` through `Pod 5`).

## Mandatory Execution Lifecycle

### Step 1: Context & Boundary Lock
1. Read `AGENTS.md` and your assigned `./plans/0X-podX-*.md` file in full.
2. Verify your active Git branch matches the pod branch specified in the plan (`git checkout -b feat/podX-...`).
3. Confirm the **Strict Non-Goals** section of your plan file. **Never modify files in another pod's `app/slices/podY_*/` or `app/frontend/src/features/podY_*/` directory.**

### Step 2: RED Phase (Write Failing Contract & Integration Tests First)
1. Open your pod's dedicated test file (`tests/unit/test_podX_*.py`).
2. Implement the deterministic pytest unit and PostgreSQL 16 (`testcontainers`) contract tests specified in Section 4 of your plan.
3. Run `uv run pytest tests/unit/test_podX_*.py` and confirm the new tests fail for the expected missing implementation reason.

### Step 3: GREEN Phase (Thin Vertical Implementation)
Implement the slice vertically inside your owned directories:
1. **Data / Repository Layer:** `app/slices/podX_*/repository.py` (using SQLAlchemy 2.0 async sessions against the 6 core tables in `app/core/models.py`).
2. **MCP Server / Tool Layer:** `app/slices/podX_*/mcp_tools.py` (enforcing `aiolimiter` token buckets and `propose_*` vs `commit_*` separation).
3. **ADK Specialist Sub-Agent & `AgentTool`:** `app/slices/podX_*/sub_agent.py` (exporting `<pod>_agent_tool` for registration in `app/agent.py`).
4. **FastAPI Slice Router:** `app/slices/podX_*/router.py` (mounted by `app/fast_api_app.py`).
5. **React UI Feature Widget:** `app/frontend/src/features/podX_*/` (typed TypeScript SSE widget component).

### Step 4: Deterministic Code Verification Gate
Run all three checks and require exit code `0`:
```bash
uv run pytest tests/unit/test_podX_*.py -v
uv run ruff check app/slices/podX_*/ tests/unit/test_podX_*.py
uv run mypy app/slices/podX_*/
```

### Step 5: `agents-cli` Behavioral Evaluation Gate
Invoke the `elevate-eval-runner` skill to verify your slice's cases in `tests/eval/datasets/eval-single-turn.json` and `tests/eval/datasets/eval-multi-turn.json`:
```bash
agents-cli eval run --config tests/eval/eval_config.yaml
```
Confirm zero regressions in `multi_turn_task_success`, `multi_turn_tool_use_quality`, `grounding`, and `safety` before committing your branch.
