from __future__ import annotations

import argparse
import os
from pathlib import Path


def _load_database_url() -> str:
    value = os.environ.get("DATABASE_URL") or _database_url_from_env_file()
    if not value:
        raise SystemExit("DATABASE_URL is not set.")
    os.environ["DATABASE_URL"] = value
    return value


def _database_url_from_env_file() -> str | None:
    backend_dir = Path(__file__).resolve().parents[2]
    env_path = backend_dir / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator and key.strip() == "DATABASE_URL":
            return value.strip().strip('"').strip("'")
    return None


def _require_confirmation(command: str, *, yes: bool) -> None:
    if not yes:
        raise SystemExit(f"Refusing to run {command!r} without --yes.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage the productivity database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("create-db", help="Create the configured database.")
    subparsers.add_parser("migrate", help="Create missing tables from app models.")
    subparsers.add_parser("seed", help="Seed example development data.")

    setup_parser = subparsers.add_parser(
        "setup", help="Create the database and run migrations."
    )
    setup_parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed example data after migration.",
    )

    reset_parser = subparsers.add_parser(
        "reset", help="Drop and recreate all tables."
    )
    reset_parser.add_argument("--yes", action="store_true", help="Confirm reset.")
    reset_parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed example data after reset.",
    )

    drop_tables_parser = subparsers.add_parser(
        "drop-tables", help="Drop all app tables."
    )
    drop_tables_parser.add_argument(
        "--yes", action="store_true", help="Confirm table drop."
    )

    drop_db_parser = subparsers.add_parser(
        "drop-db", help="Drop the configured database."
    )
    drop_db_parser.add_argument(
        "--yes", action="store_true", help="Confirm database drop."
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_url = _load_database_url()

    from sqlalchemy.exc import OperationalError

    from app.db import management
    from app.db.seeder import seed_example_data

    try:
        if args.command == "create-db":
            management.create_database(database_url)
        elif args.command == "migrate":
            management.migrate()
        elif args.command == "seed":
            seed_example_data()
        elif args.command == "setup":
            management.create_database(database_url)
            management.migrate()
            if args.seed:
                seed_example_data()
        elif args.command == "reset":
            _require_confirmation(args.command, yes=args.yes)
            management.reset_tables()
            if args.seed:
                seed_example_data()
        elif args.command == "drop-tables":
            _require_confirmation(args.command, yes=args.yes)
            management.drop_tables()
        elif args.command == "drop-db":
            _require_confirmation(args.command, yes=args.yes)
            management.drop_database(database_url)
    except OperationalError as exc:
        raise SystemExit(f"Database connection failed: {exc}") from exc


if __name__ == "__main__":
    main()
