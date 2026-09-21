"""SQLAlchemy 2.0 Async Repository for Pod 3 HITL Proposals & Audit Logs (app/slices/pod3_workweek_leave/repository.py)."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AuditTrailLog, HITLProposal

_PROPOSALS_BY_ID: dict[str, HITLProposal] = {}
_PROPOSALS_BY_IDEMPOTENCY: dict[str, HITLProposal] = {}
_AUDIT_LOGS: list[AuditTrailLog] = []


def clear_repository_state() -> None:
    """Clears in-memory repository state for deterministic unit testing."""
    _PROPOSALS_BY_ID.clear()
    _PROPOSALS_BY_IDEMPOTENCY.clear()
    _AUDIT_LOGS.clear()


class HITLProposalRepository:
    """Repository persisting HITLProposal and AuditTrailLog records in PostgreSQL 16."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self._db = db_session

    async def get_by_id(self, proposal_id: str) -> HITLProposal | None:
        """Fetches a HITLProposal by primary key from PostgreSQL 16 or active session cache."""
        if self._db is not None:
            result = await self._db.execute(
                select(HITLProposal).where(HITLProposal.proposal_id == proposal_id)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                return row
        return _PROPOSALS_BY_ID.get(str(proposal_id))

    async def get_active_by_idempotency_key(
        self,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> HITLProposal | None:
        """Returns an active PENDING proposal matching idempotency_key within the 15-min TTL window."""
        current_time = now or datetime.now(UTC)
        if self._db is not None:
            result = await self._db.execute(
                select(HITLProposal).where(
                    HITLProposal.idempotency_key == idempotency_key,
                    HITLProposal.status == "PENDING",
                    HITLProposal.expires_at > current_time,
                )
            )
            row = result.scalar_one_or_none()
            if row is not None:
                return row

        existing = _PROPOSALS_BY_IDEMPOTENCY.get(idempotency_key)
        if existing is not None and existing.status == "PENDING" and existing.expires_at > current_time:
            return existing
        return None

    async def save(self, proposal: HITLProposal) -> HITLProposal:
        """Persists a HITLProposal record to PostgreSQL 16 (`hitl_proposals` table)."""
        proposal_id_str = str(proposal.proposal_id)
        _PROPOSALS_BY_ID[proposal_id_str] = proposal
        _PROPOSALS_BY_IDEMPOTENCY[proposal.idempotency_key] = proposal

        if self._db is not None:
            self._db.add(proposal)
            await self._db.commit()
        return proposal

    async def record_audit_log(
        self,
        pseudonym_hash: str,
        action_type: str,
        status: str,
        metadata_json: dict[str, Any],
    ) -> AuditTrailLog:
        """Appends an immutable compliance record to `audit_trail_logs`."""
        log_entry = AuditTrailLog(
            log_id=uuid4(),
            pseudonym_hash=pseudonym_hash,
            action_type=action_type,
            target_system="WORKWEEK_HRIS",
            status=status,
            metadata_json=metadata_json,
            created_at=datetime.now(UTC),
        )
        _AUDIT_LOGS.append(log_entry)
        if self._db is not None:
            self._db.add(log_entry)
            await self._db.commit()
        return log_entry
