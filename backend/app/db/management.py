from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _maintenance_url(database_url: str):
    url = make_url(database_url)
    database_name = url.database
    if not database_name:
        raise ValueError("DATABASE_URL must include a database name")
    return url.set(database="postgres"), database_name


def create_database(database_url: str) -> None:
    maintenance_url, database_name = _maintenance_url(database_url)
    maintenance_engine = create_engine(
        maintenance_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True
    )
    with maintenance_engine.connect() as connection:
        exists = connection.execute(
            text("select 1 from pg_database where datname = :name"),
            {"name": database_name},
        ).scalar()
        if exists:
            print(f"Database {database_name!r} already exists.")
            return
        connection.execute(text(f"create database {_quote_identifier(database_name)}"))
        print(f"Created database {database_name!r}.")


def drop_database(database_url: str) -> None:
    maintenance_url, database_name = _maintenance_url(database_url)
    maintenance_engine = create_engine(
        maintenance_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True
    )
    with maintenance_engine.connect() as connection:
        connection.execute(
            text(
                """
                select pg_terminate_backend(pid)
                from pg_stat_activity
                where datname = :name and pid <> pg_backend_pid()
                """
            ),
            {"name": database_name},
        )
        connection.execute(
            text(f"drop database if exists {_quote_identifier(database_name)}")
        )
        print(f"Dropped database {database_name!r}.")


def migrate() -> None:
    from app import models  # noqa: F401
    from app.db.base import Base, engine

    Base.metadata.create_all(bind=engine)
    print("Created missing tables.")


def drop_tables() -> None:
    from app import models  # noqa: F401
    from app.db.base import Base, engine

    Base.metadata.drop_all(bind=engine)
    print("Dropped tables.")


def reset_tables() -> None:
    drop_tables()
    migrate()
