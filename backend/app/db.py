"""SQLAlchemy engine/session. Defaults to a local SQLite file so the app
runs with zero external services; point DATABASE_URL at Postgres for a
production-like setup (see docker-compose.yml) — same ORM layer either way.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

DATABASE_URL = get_settings().database_url
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    from app.models import orm  # noqa: F401  (registers tables on Base)

    Base.metadata.create_all(bind=engine)
