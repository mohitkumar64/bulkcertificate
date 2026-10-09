"""SQLAlchemy database setup — engine, session factory, and table creation."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from bulkcertificate.config import DATABASE_URL


# Minimal declarative base — models inherit from this.
class Base(DeclarativeBase):
    pass


# Module-level state — initialised lazily by init_db() or get_engine().
_engine = None
_SessionLocal = None


def get_engine():
    """Return the engine, creating it on first call."""
    global _engine
    if _engine is None:
        init_db()
    return _engine


def get_session_factory():
    """Return the session factory, creating it on first call."""
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    return _SessionLocal


def init_db(url: str | None = None):
    """Initialise engine and session factory.

    Args:
        url: Override the DATABASE_URL (useful for tests).
             If None, uses the value from config.
    """
    global _engine, _SessionLocal

    db_url = url or DATABASE_URL

    connect_args = {}
    extra_kwargs = {}

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # In-memory SQLite needs StaticPool so all connections share the same DB.
        if ":memory:" in db_url:
            extra_kwargs["poolclass"] = StaticPool
        else:
            from pathlib import Path

            db_path_str = db_url.replace("sqlite:////", "/").replace("sqlite:///", "")
            Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(db_url, connect_args=connect_args, **extra_kwargs)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def create_tables():
    """Create all tables that inherit from Base."""
    from bulkcertificate.models import job  # noqa: F401 — registers the table

    Base.metadata.create_all(bind=get_engine())


def get_db():
    """Yield a session then close it — used as a FastAPI dependency."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
