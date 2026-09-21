---
name: elevate-eval-runner
description: Organizes, executes, and grades the repository's evaluation suite in tests/eval/ using the official Google agents-cli format required by the Elevate Evaluator (Agent Evaluation tab). Use when adding evaluation cases, running `agents-cli eval run`, or updating tests/eval/evaluation_report.md.
---

# Elevate Evaluator & `agents-cli` Evaluation Workflow

This repository adheres strictly to the prescribed `agents-cli` evaluation directory format required by the Elevate Evaluator (**Agent Evaluation** tab):

```text
tests/
└── eval/
    ├── datasets/
    │   ├── eval-single-turn.json
    │   └── eval-multi-turn.json
    ├── eval_config.yaml
    └── evaluation_report.md
```

## 1. Running the Evaluation Suite

Always run both deterministic unit/contract tests AND `agents-cli` behavioral evaluations before opening a PR:

```bash
# 1. Deterministic Code & Contract Verification (Fast pytest suite)
uv run pytest tests/unit/ -v

# 2. Behavioral Agent Evaluation via agents-cli
agents-cli eval run --config tests/eval/eval_config.yaml
```

To evaluate a specific dataset file during pod development:
```bash
# Single-turn Policy RAG, Entitlement & Safety evaluation
agents-cli eval run \
  --dataset tests/eval/datasets/eval-single-turn.json \
  --config tests/eval/eval_config.yaml

# Multi-turn HITL Approval, 2-System Saga Rollback & Warm Handoff evaluation
agents-cli eval run \
  --dataset tests/eval/datasets/eval-multi-turn.json \
  --config tests/eval/eval_config.yaml
```

## 2. Mandatory Pass Thresholds (`tests/eval/evaluation_report.md`)

Every PR must maintain or improve the following benchmark gates documented in `tests/eval/evaluation_report.md`:
- `multi_turn_task_success`: **$\ge 0.95$** (`95%`)
- `multi_turn_trajectory_quality`: **$\ge 0.95$** (`95%`)
- `multi_turn_tool_use_quality`: **$\ge 0.95$** (`95%`)
- `hallucination` / `grounding` (Policy RAG citations): **$\ge 0.96$** (`96%`)
- `safety` (Prompt injection & PII redaction compliance): **$1.00$** (`100%`)
- Custom `hitl_two_phase_gate_compliance`: **$1.00$** (`100%` — zero direct mutations without human confirmation)
- Custom `pre_retrieval_entitlement_compliance`: **$1.00$** (`100%` — zero cross-country or cross-role policy leakage)
