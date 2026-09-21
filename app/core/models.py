"""Canonical 6-Table PostgreSQL 16 + pgvector Schema (app/core/models.py)."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all 6 core PostgreSQL 16 tables."""


class UserSalt(Base):
    """Table 1: Per-employee KMS-wrapped cryptographic salt for GDPR Art. 17 crypto-shredding."""

    __tablename__ = "user_salts"

    employee_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kms_key_resource_name: Mapped[str] = mapped_column(Text, nullable=False)
    user_salt: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    destroyed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionRecord(Base):
    """Table 2: Active employee session keyed by HMAC-SHA256 pseudonym_hash."""

    __tablename__ = "sessions"

    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    pseudonym_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_manager: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConversationTurn(Base):
    """Table 3: DLP-redacted transcript turns with optional encrypted PII payload."""

    __tablename__ = "conversation_turns"

    turn_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.session_id"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    redacted_content: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_pii_blob: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HITLProposal(Base):
    """Table 4: Two-Phase Human-in-the-Loop Proposal state (15-minute TTL + SHA-256 idempotency)."""

    __tablename__ = "hitl_proposals"

    proposal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.session_id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditTrailLog(Base):
    """Table 5: Immutable 7-year compliance ledger containing zero raw PII."""

    __tablename__ = "audit_trail_logs"

    log_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    pseudonym_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_system: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    erasure_receipt_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HRPolicyChunk(Base):
    """Table 6: Hybrid pgvector + Full-Text policy chunks with mandatory pre-retrieval entitlement columns."""

    __tablename__ = "hr_policy_chunks"

    chunk_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(64), nullable=False)
    section_anchor: Mapped[str] = mapped_column(String(64), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), index=True, nullable=False)
    min_role: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
