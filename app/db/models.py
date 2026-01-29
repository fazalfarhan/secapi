"""Database models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tier: Mapped[Literal["free", "pro", "enterprise"]] = mapped_column(
        String(50), default="free", nullable=False
    )

    # Relationships
    scans: Mapped[list["Scan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_usage: Mapped[list["ApiUsage"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    rate_limits: Mapped[list["RateLimit"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Scan(Base, TimestampMixin):
    """Scan model."""

    __tablename__ = "scans"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_type: Mapped[Literal["trivy"]] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[Literal["pending", "running", "completed", "failed"]] = mapped_column(
        String(50), default="pending", nullable=False
    )
    input_data: Mapped[dict | None] = mapped_column(Text, nullable=True)
    results: Mapped[dict | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="scans")


class ApiUsage(Base, TimestampMixin):
    """API usage model."""

    __tablename__ = "api_usage"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    response_time_ms: Mapped[int] = mapped_column(nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_usage")


class RateLimit(Base):
    """Rate limit model."""

    __tablename__ = "rate_limits"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    scans_count: Mapped[int] = mapped_column(default=0, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_reset: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="rate_limits")
