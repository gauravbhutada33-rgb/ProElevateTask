# syntax=docker/dockerfile:1
# Production Cloud Run Dockerfile — Enterprise HR Agentic Solution (MVP 1)
# Enforces Alex Rivera (IT Director) Safeguards:
#   1. Slim image (<250MB) with zero in-process ONNX models for <1.5s Cloud Run cold-start.
#   2. Physical build-time exclusion of `tests/` (and MockIdP) from the production container.
#   3. Non-root execution (`appuser`) on Cloud Run default PORT=8080.

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml README.md SDD.md ./
COPY app ./app

# Install production dependencies only (--no-dev excludes test/mock packages)
RUN uv sync --no-dev

FROM python:3.12-slim AS runtime

RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 --gid appgroup --shell /sbin/nologin --create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/app /app/app
COPY --from=builder --chown=appuser:appgroup /app/agents-cli-manifest.yaml /app/SDD.md /app/AGENTS.md ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GEMINI_FLASH_MODEL="gemini-3.6-flash" \
    GEMINI_PRO_MODEL="gemini-3.6-pro" \
    VERTEX_AI_ZERO_DATA_RETENTION="true"

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
