"""SQLAlchemy ORM models matching the multi-tenant RDS schema."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# Use generic UUID for SQLite compat in tests, PG_UUID in production
def _uuid_col(primary_key=False, **kwargs):
    return mapped_column(
        String(36) if False else Text,  # always use Text for portability
        primary_key=primary_key,
        default=lambda: str(uuid.uuid4()),
        **kwargs,
    )


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_by: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships: Mapped[list["Membership"]
                        ] = relationship(back_populates="tenant")
    vendors: Mapped[list["Vendor"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    cognito_sub: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships: Mapped[list["Membership"]
                        ] = relationship(back_populates="user")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id"),)

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(Text)
    contact_phone: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="vendors")
    documents: Mapped[list["Document"]] = relationship(back_populates="vendor")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "vendors.id", ondelete="CASCADE"), nullable=False)
    document_type: Mapped[str | None] = mapped_column(Text, default="other")
    title: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="uploaded")
    current_version_no: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1)
    created_by: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor: Mapped["Vendor"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]
                     ] = relationship(back_populates="document")


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_no"),)

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="uploaded")
    s3_bucket: Mapped[str | None] = mapped_column(Text)
    s3_key: Mapped[str | None] = mapped_column(Text)
    original_filename: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    document: Mapped["Document"] = relationship(back_populates="versions")


class CheckRequest(Base):
    __tablename__ = "check_requests"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    submitted_by: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("vendors.id"))
    input_type: Mapped[str] = mapped_column(Text, nullable=False)
    raw_input_text: Mapped[str | None] = mapped_column(Text)
    vendor_name: Mapped[str | None] = mapped_column(Text)
    vendor_contact_email: Mapped[str | None] = mapped_column(Text)
    vendor_contact_phone: Mapped[str | None] = mapped_column(Text)
    bank_name: Mapped[str | None] = mapped_column(Text)
    bank_account_hash: Mapped[str | None] = mapped_column(Text)
    bank_routing_hash: Mapped[str | None] = mapped_column(Text)
    bank_account_masked: Mapped[str | None] = mapped_column(Text)
    bank_routing_masked: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="processing")
    verdict: Mapped[str | None] = mapped_column(Text)
    verdict_explanation: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    risk_score: Mapped[int | None] = mapped_column(Integer)
    prior_check_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("check_requests.id"))
    bank_details_changed: Mapped[bool | None] = mapped_column(Boolean)
    analysis_error: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[str | None] = mapped_column(
        Text, ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    signals: Mapped[list["RiskSignal"]] = relationship(
        back_populates="check_request")


class RiskSignal(Base):
    __tablename__ = "risk_signals"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    document_version_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("document_versions.id", ondelete="CASCADE"))
    check_request_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("check_requests.id", ondelete="CASCADE"))
    signal_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[str | None] = mapped_column("metadata", Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)

    check_request: Mapped["CheckRequest | None"] = relationship(
        back_populates="signals")


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("documents.id", ondelete="CASCADE"))
    document_version_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("document_versions.id", ondelete="CASCADE"))
    check_request_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("check_requests.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="open")
    assigned_to: Mapped[str | None] = mapped_column(
        Text, ForeignKey("users.id"))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    resolution: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[str | None] = mapped_column(
        Text, ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(Text, ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(
        Text)  # JSON string; JSONB in Postgres
    ip_address: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)


class MetricEvent(Base):
    __tablename__ = "metric_events"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(Text, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(Text)
    entity_id: Mapped[str | None] = mapped_column(Text)
    value: Mapped[float | None] = mapped_column(
        Integer)  # using Integer for SQLite compat
    metadata_: Mapped[str | None] = mapped_column("metadata", Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow)
