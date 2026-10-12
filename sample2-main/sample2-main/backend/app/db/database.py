from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    future=True,
)
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator[Session, None, None]:
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend.app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _add_missing_columns(engine, ("company_master", "invoice_header"))


def _add_missing_columns(bind, table_names: tuple[str, ...]) -> None:
    # create_all never alters existing tables, so columns added later are appended here.
    inspector = inspect(bind)
    with bind.begin() as connection:
        for table_name in table_names:
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column in Base.metadata.tables[table_name].columns:
                if column.name in existing:
                    continue
                column_type = column.type.compile(dialect=bind.dialect)
                default = f" DEFAULT {column.server_default.arg}" if column.server_default is not None else ""
                connection.execute(text(f'ALTER TABLE {table_name} ADD COLUMN "{column.name}" {column_type}{default}'))
