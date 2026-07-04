"""Database connection helpers for PostgreSQL (SQLAlchemy) and MongoDB (PyMongo)."""

from contextlib import contextmanager

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import (
    MONGODB_COLLECTION,
    MONGODB_DATABASE,
    MONGODB_URI,
    POSTGRES_URL,
)

_engine: Engine | None = None
_session_factory: sessionmaker | None = None
_mongo_client: MongoClient | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False)
    return _session_factory


@contextmanager
def postgres_session():
    session: Session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGODB_URI)
    return _mongo_client


def get_mongo_db() -> Database:
    return get_mongo_client()[MONGODB_DATABASE]


def get_mongo_collection() -> Collection:
    collection = get_mongo_db()[MONGODB_COLLECTION]
    collection.create_index("record_id", unique=True)
    collection.create_index("sale_date")
    return collection


def ping_postgres() -> bool:
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


def ping_mongodb() -> bool:
    get_mongo_client().admin.command("ping")
    return True
