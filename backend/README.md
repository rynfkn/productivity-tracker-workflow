# Productivity Tracker Backend

## Database Recovery

This app uses PostgreSQL through SQLAlchemy. The schema is defined in
`app/models/`, and the API also creates missing tables on startup with
`Base.metadata.create_all(bind=engine)`.

The current `migrate` command is a schema bootstrap command: it creates missing
tables from the SQLAlchemy models. It is not a versioned migration system, and
it will not alter existing columns the way Alembic migrations would.

Lost table structure can be rebuilt from the models. Lost data can only be
recovered from a database backup, provider snapshot, point-in-time recovery, or
an exported dump.

From the `backend/` directory:

```bash
python -m app.db.cli setup
```

Useful commands:

```bash
# Create the configured PostgreSQL database if it does not exist.
python -m app.db.cli create-db

# Create missing tables without deleting anything.
python -m app.db.cli migrate

# Create the database, create missing tables, and seed example data.
python -m app.db.cli setup --seed

# Add dashboard-friendly development rows, completions, habit history, and
# reminder schedules.
python -m app.db.cli seed

# Drop and recreate all tables, then seed example data. This deletes table data.
python -m app.db.cli reset --yes --seed
```

Dangerous commands require `--yes`:

```bash
python -m app.db.cli reset --yes
python -m app.db.cli drop-tables --yes
python -m app.db.cli drop-db --yes
```

The same commands can be run in Docker by overriding the container command:

```bash
docker run --env-file backend/.env <image-name> python -m app.db.cli setup --seed
```

The script reads `DATABASE_URL` from `.env`, the same as the backend app.
`backend/scripts/manage_db.py` is kept as a compatibility wrapper around
`python -m app.db.cli`.
