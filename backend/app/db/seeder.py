from __future__ import annotations

from datetime import datetime, timedelta, timezone


def seed_example_data() -> None:
    from app.db.base import SessionLocal
    from app.models import Activity
    from app.repositories import reminder_schedule_repo

    now = datetime.now(timezone.utc).replace(microsecond=0)
    rows = [
        Activity(
            activity_name="Drink water",
            activity_kind="habit",
            start_at=now + timedelta(minutes=5),
            deadline_at=now + timedelta(hours=8),
            reminder_offsets_minutes=[30],
            status="pending",
        ),
        Activity(
            activity_name="Review weekly priorities",
            activity_kind="reminder",
            deadline_at=now + timedelta(days=1),
            reminder_offsets_minutes=[60, 30],
            status="pending",
        ),
    ]

    db = SessionLocal()
    try:
        created = 0
        for row in rows:
            existing = (
                db.query(Activity)
                .filter(Activity.activity_name == row.activity_name)
                .filter(Activity.deleted_at.is_(None))
                .first()
            )
            if existing:
                continue

            db.add(row)
            db.commit()
            db.refresh(row)
            reminder_schedule_repo.create_schedule_for_activity(
                db, row, min_remind_at=now
            )
            created += 1

        print(f"Seeded {created} example activities.")
    finally:
        db.close()
