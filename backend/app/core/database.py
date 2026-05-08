from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


def database_url() -> str:
    settings = get_settings()
    return settings.database_url if "pytest" not in __import__("sys").modules else settings.local_database_url


def engine_kwargs(url: str) -> dict[str, object]:
    if url.startswith("sqlite"):
        return {"connect_args": {"timeout": 3}}
    if url.startswith(("postgresql", "postgres")):
        return {"connect_args": {"connect_timeout": 3}}
    return {}


url = database_url()
engine = create_engine(url, pool_pre_ping=True, **engine_kwargs(url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
