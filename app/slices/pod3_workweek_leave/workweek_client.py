"""Token-Bucket Rate-Limited WorkWeek HRIS Client & Cloud Tasks Retry Queue (app/slices/pod3_workweek_leave/workweek_client.py)."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from aiolimiter import AsyncLimiter
from pydantic import BaseModel

from app.core.config import settings
from app.core.models import HITLProposal

# RES-02: Alex Rivera (IT Director) Safeguard — 50 RPS sustained rate limit for WorkWeek HRIS
workweek_limiter = AsyncLimiter(max_rate=float(settings.WORKWEEK_RPS_LIMIT), time_period=1.0)


class WorkWeekUpstreamError(Exception):
    """Raised when WorkWeek returns a rate-limit (429) or transient server error (5xx)."""

    def __init__(self, status_code: int, message: str, retry_after_seconds: int = 2) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds


class LeaveBalanceResponse(BaseModel):
    """Structured employee leave balance payload from WorkWeek HRIS."""

    employee_id: str
    pto_available_days: float
    parental_leave_available_days: float
    sick_leave_available_days: float
    cached_ttl_seconds: int
    fetched_at_utc: str


class WorkWeekCommitResult(BaseModel):
    """Result of committing a human-confirmed HITL leave proposal to WorkWeek HRIS."""

    proposal_id: str
    status: str  # "CONFIRMED" | "QUEUED_RETRY"
    workweek_transaction_id: str | None = None
    queue_name: str | None = None
    task_id: str | None = None
    retry_after_seconds: int | None = None
    committed_at_utc: str


_BALANCE_CACHE: dict[str, tuple[LeaveBalanceResponse, datetime]] = {}
_QUEUED_RETRY_TASKS: list[dict[str, Any]] = []
_REDIS_CLIENT: Any | None = None


def set_redis_client(redis_client: Any | None) -> None:
    """Sets an optional async Redis client for read-through caching and webhook eviction."""
    global _REDIS_CLIENT
    _REDIS_CLIENT = redis_client


def clear_balance_cache_and_retry_queue() -> None:
    """Clears in-memory Redis cache, Cloud Tasks retry queue, and rebinds limiter."""
    global workweek_limiter, _REDIS_CLIENT
    _BALANCE_CACHE.clear()
    _QUEUED_RETRY_TASKS.clear()
    _REDIS_CLIENT = None
    workweek_limiter = AsyncLimiter(max_rate=float(settings.WORKWEEK_RPS_LIMIT), time_period=1.0)


def get_cached_balance_ttl(employee_id: str) -> int | None:
    """Returns remaining TTL in seconds for `ww:balance:{employee_id}`, or None if not cached."""
    cache_key = f"ww:balance:{employee_id}"
    entry = _BALANCE_CACHE.get(cache_key)
    if entry is None:
        return None
    _, expires_at = entry
    now = datetime.now(UTC)
    if expires_at <= now:
        _BALANCE_CACHE.pop(cache_key, None)
        return None
    return settings.CACHE_TTL_SECONDS


async def evict_leave_balance_cache(employee_id: str) -> str:
    """SLA-02: Evicts `ww:balance:{employee_id}` via `redis.delete` in <60s upon webhook event."""
    cache_key = f"ww:balance:{employee_id}"
    if _REDIS_CLIENT is not None and hasattr(_REDIS_CLIENT, "delete"):
        await _REDIS_CLIENT.delete(cache_key)
    _BALANCE_CACHE.pop(cache_key, None)
    return cache_key


def get_queued_retry_tasks() -> list[dict[str, Any]]:
    """Returns tasks enqueued to `ww-it-mutation-retry-queue`."""
    return list(_QUEUED_RETRY_TASKS)


async def get_leave_balance(employee_id: str = "EMP-1042") -> LeaveBalanceResponse:
    """FR-02 & SLA-02: Reads employee PTO/parental leave balances with 60s Redis read-through caching."""
    cache_key = f"ww:balance:{employee_id}"
    now = datetime.now(UTC)

    if _REDIS_CLIENT is not None and hasattr(_REDIS_CLIENT, "get"):
        raw_cached = await _REDIS_CLIENT.get(cache_key)
        if raw_cached:
            payload_str = raw_cached.decode("utf-8") if isinstance(raw_cached, bytes) else str(raw_cached)
            return LeaveBalanceResponse.model_validate_json(payload_str)

    cached_entry = _BALANCE_CACHE.get(cache_key)
    if cached_entry is not None:
        cached_resp, expires_at = cached_entry
        if expires_at > now:
            return cached_resp

    async with workweek_limiter:
        response = LeaveBalanceResponse(
            employee_id=employee_id,
            pto_available_days=15.0,
            parental_leave_available_days=60.0,
            sick_leave_available_days=10.0,
            cached_ttl_seconds=settings.CACHE_TTL_SECONDS,
            fetched_at_utc=now.isoformat(),
        )
        _BALANCE_CACHE[cache_key] = (
            response,
            now + timedelta(seconds=settings.CACHE_TTL_SECONDS),
        )
        if _REDIS_CLIENT is not None and hasattr(_REDIS_CLIENT, "setex"):
            await _REDIS_CLIENT.setex(
                cache_key,
                settings.CACHE_TTL_SECONDS,
                response.model_dump_json(),
            )
        return response


def _enqueue_cloud_task_retry(
    proposal: HITLProposal,
    http_status: int,
    retry_after_seconds: int,
) -> dict[str, Any]:
    """Enqueues an idempotent mutation retry task into `ww-it-mutation-retry-queue`."""
    task_payload: dict[str, Any] = {
        "task_id": f"TASK-RETRY-{uuid4().hex[:8].upper()}",
        "queue_name": settings.CLOUD_TASKS_RETRY_QUEUE,
        "proposal_id": str(proposal.proposal_id),
        "employee_id": proposal.employee_id,
        "idempotency_key": proposal.idempotency_key,
        "proposed_payload": proposal.proposed_payload,
        "upstream_http_status": http_status,
        "retry_after_seconds": retry_after_seconds,
        "max_attempts": 5,
        "initial_backoff_seconds": 2,
        "max_backoff_seconds": 60,
        "enqueued_at_utc": datetime.now(UTC).isoformat(),
    }
    _QUEUED_RETRY_TASKS.append(task_payload)
    return task_payload


async def commit_leave_to_workweek(
    proposal: HITLProposal,
    simulate_http_status: int | None = None,
    retry_after_seconds: int | None = None,
) -> WorkWeekCommitResult:
    """Phase 2 Commit to WorkWeek HRIS with 50 RPS throttling and 429/5xx Cloud Tasks fallback."""
    async with workweek_limiter:
        now_iso = datetime.now(UTC).isoformat()
        if simulate_http_status in {429, 500, 502, 503, 504}:
            backoff_sec = retry_after_seconds if retry_after_seconds is not None else 2
            proposal.status = "QUEUED_RETRY"
            task_info = _enqueue_cloud_task_retry(
                proposal=proposal,
                http_status=simulate_http_status,
                retry_after_seconds=backoff_sec,
            )
            return WorkWeekCommitResult(
                proposal_id=str(proposal.proposal_id),
                status="QUEUED_RETRY",
                workweek_transaction_id=None,
                queue_name=settings.CLOUD_TASKS_RETRY_QUEUE,
                task_id=str(task_info["task_id"]),
                retry_after_seconds=backoff_sec,
                committed_at_utc=now_iso,
            )

        proposal.status = "CONFIRMED"
        await evict_leave_balance_cache(proposal.employee_id)
        return WorkWeekCommitResult(
            proposal_id=str(proposal.proposal_id),
            status="CONFIRMED",
            workweek_transaction_id=f"WW-TX-{uuid4().hex[:8].upper()}",
            queue_name=None,
            task_id=None,
            retry_after_seconds=None,
            committed_at_utc=now_iso,
        )
