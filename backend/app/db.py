"""SQLAlchemy engine and session for portal users/auth."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def database_url() -> str:
    default = Path(__file__).resolve().parent.parent / "var" / "portal_auth.db"
    url = os.environ.get("DATABASE_URL", f"sqlite:///{default}")
    # Render and many hosts provide postgres://; SQLAlchemy expects postgresql://
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


class Base(DeclarativeBase):
    pass


def _engine():
    url = database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = _engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    # Import models so metadata is registered
    from app import models  # noqa: F401

    if engine.url.drivername.startswith("sqlite") and engine.url.database:
        Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
