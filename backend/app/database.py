from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def ensure_sqlite_columns() -> None:
    """Add columns introduced after the initial prototype without a migration tool."""
    if not settings.database_url.startswith("sqlite"):
        return
    statements = [
        ("observations", "interpretation", "ALTER TABLE observations ADD COLUMN interpretation VARCHAR(32)"),
    ]
    with engine.begin() as conn:
        for table, column, ddl in statements:
            exists = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")).fetchone()
            if not exists:
                continue
            cols = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}
            if column not in cols:
                conn.execute(text(ddl))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
