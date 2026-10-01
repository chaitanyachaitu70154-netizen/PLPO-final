"""
Database Session and Engine Management for Phase 4.
Handles connection pooling, engine initialization, dialect detection (PostgreSQL vs SQLite),
and transactional session lifecycles.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

logger = logging.getLogger("plpo.db")

# Default local database path if no PostgreSQL connection is provided
DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "plpo.db")
DEFAULT_DATABASE_URL = f"sqlite:///{os.path.abspath(DEFAULT_SQLITE_PATH).replace(os.sep, '/')}"

_ENGINE: Engine = None
_SESSION_FACTORY = None

def get_database_url() -> str:
    """Retrieve and normalize database URL from environment or fallback to SQLite."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        return DEFAULT_DATABASE_URL
    
    # Heroku / AWS RDS legacy dialect fix
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def is_postgres(engine: Engine = None) -> bool:
    """Check if target database dialect is PostgreSQL."""
    eng = engine or get_engine()
    return eng.dialect.name == "postgresql"

def get_engine() -> Engine:
    """Initialize or return singleton SQLAlchemy Engine with production pool parameters."""
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    url = get_database_url()
    
    if url.startswith("sqlite"):
        # Ensure target data directory exists
        os.makedirs(os.path.dirname(DEFAULT_SQLITE_PATH), exist_ok=True)
        
        _ENGINE = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False
        )

        # Optimize SQLite for multi-threaded concurrency (WAL mode + foreign keys)
        @event.listens_for(_ENGINE, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info(f"Initialized SQLite database at {url}")
    else:
        # PostgreSQL with production connection pooling
        _ENGINE = create_engine(
            url,
            pool_size=int(os.environ.get("DB_POOL_SIZE", "10")),
            max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "20")),
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            echo=False
        )
        logger.info("Initialized PostgreSQL database engine with connection pooling")

    return _ENGINE

def get_session_factory():
    """Retrieve or create thread-safe sessionmaker."""
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        engine = get_engine()
        _SESSION_FACTORY = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False
        )
    return _SESSION_FACTORY

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session scope."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Database transaction rolled back due to error: {exc}", exc_info=True)
        raise
    finally:
        session.close()

def init_database() -> None:
    """Create all tables and initialize extensions (e.g. pgvector on PostgreSQL)."""
    from core.db.models import Base
    engine = get_engine()

    if is_postgres(engine):
        # Enable pgvector extension if PostgreSQL
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("Verified/Enabled PostgreSQL 'vector' extension")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension (may require superuser or pgvector installed): {e}")

    Base.metadata.create_all(bind=engine)
    logger.info("Synchronized database schema and indexes.")
