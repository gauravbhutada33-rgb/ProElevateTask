"""Live Streamable-HTTP JSON-RPC 2.0 MCP Client for WorkWeek & ServiceImmediately (app/core/mcp_client.py).

Connects to:
  - WorkWeek MCP (`https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/`, 50 RPS limiter)
  - ServiceImmediately MCP (`https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/`, 25 RPS limiter)
Authenticates via `Authorization: Bearer <MCP_AUTH_TOKEN>` (Scoped to `EMP-824` / Gururay Employee).
Enforces Two-Phase HITL (`propose_*` vs `commit_*`) for all mutating tools.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx
from aiolimiter import AsyncLimiter

from app.core.config import settings

# Alex Rivera (IT Director) Safeguard: Explicit Token-Bucket Rate Limiters
workweek_rate_limiter = AsyncLimiter(max_rate=settings.WORKWEEK_RPS_LIMIT, time_period=1.0)
service_immediately_rate_limiter = AsyncLimiter(
    max_rate=settings.SERVICEIMMEDIATELY_RPS_LIMIT, time_period=1.0
)

# In-memory HITL proposal staging registry (backed by PostgreSQL 16 `hitl_proposals` in DB sessions)
PENDING_HITL_PROPOSALS: dict[str, dict[str, Any]] = {}


class MockSaaSMCPClient:
    """JSON-RPC 2.0 MCP Client for WorkWeek (v1.29.0) and ServiceImmediately (v1.29.0)."""

    def __init__(
        self,
        workweek_url: str = settings.WORKWEEK_MCP_URL,
        service_immediately_url: str = settings.SERVICEIMMEDIATELY_MCP_URL,
        auth_token: str = settings.MCP_AUTH_TOKEN,
    ) -> None:
        self.workweek_url = workweek_url
        self.service_immediately_url = service_immediately_url
        self.auth_token = auth_token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

    async def _call_mcp_jsonrpc(
        self,
        endpoint_url: str,
        limiter: AsyncLimiter,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Executes a rate-limited JSON-RPC 2.0 `tools/call` against the remote MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": uuid4().hex[:8],
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        async with (
            limiter,
            httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client,
        ):
            response = await client.post(endpoint_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            body: dict[str, Any] = response.json()
            result: dict[str, Any] = body.get("result", {})
            structured = result.get("structuredContent", {})
            text_out = structured.get("result")
            if text_out is None:
                content_list = result.get("content", [])
                text_out = content_list[0].get("text", "") if content_list else ""
            return {
                "tool": tool_name,
                "is_error": bool(result.get("isError", False)),
                "result": text_out,
                "raw": result,
            }

    async def call_workweek(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invokes any of the 7 live WorkWeek MCP tools (`50 RPS` token-bucket throttled)."""
        return await self._call_mcp_jsonrpc(
            self.workweek_url, workweek_rate_limiter, tool_name, arguments
        )

    async def call_service_immediately(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Invokes any of the 4 live ServiceImmediately MCP tools (`25 RPS` token-bucket throttled)."""
        return await self._call_mcp_jsonrpc(
            self.service_immediately_url,
            service_immediately_rate_limiter,
            tool_name,
            arguments,
        )


mcp_client = MockSaaSMCPClient()


# ============================================================================
# ADK-Compatible Tool Wrappers (Read Tools + Two-Phase HITL Proposal Tools)
# ============================================================================


async def workweek_get_current_employee_id() -> dict[str, Any]:
    """Fetches the authenticated employee ID (`EMP-824`) from the live WorkWeek MCP server."""
    return await mcp_client.call_workweek("get_current_employee_id", {})


async def workweek_get_employee_balances(
    employee_id: str = settings.DEFAULT_EMPLOYEE_ID,
) -> dict[str, Any]:
    """Fetches current Vacation and Sick leave balances for `employee_id` (`EMP-824`)."""
    return await mcp_client.call_workweek("get_employee_balances", {"employee_id": employee_id})


async def workweek_get_personal_info(
    employee_id: str = settings.DEFAULT_EMPLOYEE_ID,
) -> dict[str, Any]:
    """Fetches home address and phone number for `employee_id` (`EMP-824`)."""
    return await mcp_client.call_workweek("get_personal_info", {"employee_id": employee_id})


async def workweek_get_leave_requests(
    employee_id: str = settings.DEFAULT_EMPLOYEE_ID,
) -> dict[str, Any]:
    """Fetches the history of all requested time off for `employee_id` (`EMP-824`)."""
    return await mcp_client.call_workweek("get_leave_requests", {"employee_id": employee_id})


def workweek_propose_time_off(
    start_date: str,
    end_date: str,
    leave_type: str,
    days: float,
    employee_id: str = settings.DEFAULT_EMPLOYEE_ID,
) -> dict[str, Any]:
    """Phase 1 HITL Tool: Stages a `request_time_off` proposal (`Vacation` or `Sick`) without mutating WorkWeek.

    Returns a `proposal_id` (`15-min TTL`) and `hitl_card` payload for `/api/v1/hitl/confirm`.
    """
    canonical = json.dumps(
        {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": leave_type,
            "days": days,
        },
        sort_keys=True,
    )
    idempotency_key = hashlib.sha256(f"request_time_off:{canonical}".encode()).hexdigest()
    proposal_id = f"prop-{idempotency_key[:8]}"
    expires_at = (datetime.now(UTC) + timedelta(minutes=15)).isoformat()

    proposal_record = {
        "proposal_id": proposal_id,
        "employee_id": employee_id,
        "target_mcp": "WorkWeek",
        "mcp_tool_name": "request_time_off",
        "arguments": {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": leave_type,
            "days": days,
        },
        "idempotency_key": idempotency_key,
        "status": "PENDING",
        "expires_at_utc": expires_at,
    }
    PENDING_HITL_PROPOSALS[proposal_id] = proposal_record
    return {
        "type": "hitl_card",
        **proposal_record,
    }


def workweek_propose_update_personal_info(
    address: str,
    phone: str,
    employee_id: str = settings.DEFAULT_EMPLOYEE_ID,
) -> dict[str, Any]:
    """Phase 1 HITL Tool: Stages an `update_personal_info` proposal without mutating WorkWeek."""
    canonical = json.dumps(
        {"employee_id": employee_id, "address": address, "phone": phone}, sort_keys=True
    )
    idempotency_key = hashlib.sha256(f"update_personal_info:{canonical}".encode()).hexdigest()
    proposal_id = f"prop-{idempotency_key[:8]}"
    expires_at = (datetime.now(UTC) + timedelta(minutes=15)).isoformat()

    proposal_record = {
        "proposal_id": proposal_id,
        "employee_id": employee_id,
        "target_mcp": "WorkWeek",
        "mcp_tool_name": "update_personal_info",
        "arguments": {"employee_id": employee_id, "address": address, "phone": phone},
        "idempotency_key": idempotency_key,
        "status": "PENDING",
        "expires_at_utc": expires_at,
    }
    PENDING_HITL_PROPOSALS[proposal_id] = proposal_record
    return {"type": "hitl_card", **proposal_record}


async def service_immediately_list_tickets(
    employee_id: str = settings.DEFAULT_EMPLOYEE_ID,
) -> dict[str, Any]:
    """Lists all ServiceImmediately incident tickets requested by `employee_id` (`EMP-824`)."""
    return await mcp_client.call_service_immediately("list_tickets", {"employee_id": employee_id})


def service_immediately_propose_ticket(
    category: str,
    short_description: str,
    priority: str = "3 - Moderate",
    assignment_group: str = "Service Desk",
    requested_by: str = settings.DEFAULT_EMPLOYEE_ID,
) -> dict[str, Any]:
    """Phase 1 HITL Tool: Stages a `create_ticket` proposal in ServiceImmediately (`15-min TTL`)."""
    canonical = json.dumps(
        {
            "requested_by": requested_by,
            "category": category,
            "short_description": short_description,
            "priority": priority,
            "assignment_group": assignment_group,
        },
        sort_keys=True,
    )
    idempotency_key = hashlib.sha256(f"create_ticket:{canonical}".encode()).hexdigest()
    proposal_id = f"prop-{idempotency_key[:8]}"
    expires_at = (datetime.now(UTC) + timedelta(minutes=15)).isoformat()

    proposal_record = {
        "proposal_id": proposal_id,
        "employee_id": requested_by,
        "target_mcp": "ServiceImmediately",
        "mcp_tool_name": "create_ticket",
        "arguments": {
            "requested_by": requested_by,
            "category": category,
            "short_description": short_description,
            "priority": priority,
            "assignment_group": assignment_group,
        },
        "idempotency_key": idempotency_key,
        "status": "PENDING",
        "expires_at_utc": expires_at,
    }
    PENDING_HITL_PROPOSALS[proposal_id] = proposal_record
    return {"type": "hitl_card", **proposal_record}


async def commit_confirmed_hitl_proposal(proposal_id: str) -> dict[str, Any]:
    """Phase 2 Commit Function (Invoked ONLY by `POST /api/v1/hitl/confirm` after human click)."""
    proposal = PENDING_HITL_PROPOSALS.get(proposal_id)
    if not proposal:
        return {"proposal_id": proposal_id, "status": "CONFIRMED_NO_STAGED_PAYLOAD"}

    target = proposal["target_mcp"]
    tool_name = proposal["mcp_tool_name"]
    args = proposal["arguments"]

    if target == "WorkWeek":
        mcp_res = await mcp_client.call_workweek(tool_name, args)
    else:
        mcp_res = await mcp_client.call_service_immediately(tool_name, args)

    proposal["status"] = "CONFIRMED"
    proposal["mcp_response"] = mcp_res
    return proposal
