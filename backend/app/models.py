"""ORM models for users, sessions, email tokens, and query analytics."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

ACCESS_WAITLIST_PENDING = "WAITLIST_PENDING"
ACCESS_APPROVED = "APPROVED"
ACCESS_SUSPENDED = "SUSPENDED"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), default="")
    last_name: Mapped[str] = mapped_column(String(100), default="")
    phone_country_code: Mapped[str] = mapped_column(String(8), default="")
    phone_number: Mapped[str] = mapped_column(String(32), default="")
    country_of_residence: Mapped[str] = mapped_column(String(2), default="")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    access_status: Mapped[str] = mapped_column(String(32), default=ACCESS_WAITLIST_PENDING, index=True)
    is_tester: Mapped[bool] = mapped_column(Boolean, default=False)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)

    sessions: Mapped[list[SessionToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    email_tokens: Mapped[list[EmailToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    query_events: Mapped[list[QueryEvent]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def can_run_queries(self) -> bool:
        if self.access_status == ACCESS_SUSPENDED:
            return False
        if not self.email_verified:
            return False
        return self.access_status == ACCESS_APPROVED or self.is_tester

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_country_code": self.phone_country_code,
            "phone_number": self.phone_number,
            "country_of_residence": self.country_of_residence,
            "email_verified": self.email_verified,
            "access_status": self.access_status,
            "is_tester": self.is_tester,
            "can_run_queries": self.can_run_queries(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


class SessionToken(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="sessions")


class EmailToken(Base):
    __tablename__ = "email_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(32))  # verify | reset
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="email_tokens")


class QueryEvent(Base):
    __tablename__ = "query_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    mode: Mapped[str] = mapped_column(String(16), default="")  # live | mock | error
    bytes_billed: Mapped[int] = mapped_column(BigInteger, default=0)
    bytes_processed: Mapped[int] = mapped_column(BigInteger, default=0)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(64), default="")
    sql_preview: Mapped[str] = mapped_column(String(240), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    user: Mapped[User | None] = relationship(back_populates="query_events")
