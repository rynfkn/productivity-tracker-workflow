from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Activity


def mark_overdue_habits_as_missed(db: Session, now: datetime) -> int:
    """Mark habits whose deadline has passed and are still pending as missed.
    Returns the count of rows updated."""
    rows = (
        db.query(Activity)
        .filter(Activity.activity_kind == "habit")
        .filter(Activity.status == "pending")
        .filter(Activity.deadline_at.isnot(None))
        .filter(Activity.deadline_at < now)
        .all()
    )
    for row in rows:
        row.status = "missed"
    db.commit()
    return len(rows)


def get_habit_progress(db: Session) -> list[dict]:
    """Return per-habit-name progress: total occurrences, done, missed (up to now)."""
    rows = (
        db.query(Activity)
        .filter(Activity.activity_kind == "habit")
        .filter(Activity.status.in_(["done", "missed"]))
        .all()
    )

    stats: dict[str, dict] = {}
    for row in rows:
        name = row.activity_name
        if name not in stats:
            stats[name] = {"habit_name": name, "done": 0, "missed": 0, "total": 0}
        stats[name][row.status] += 1
        stats[name]["total"] += 1

    return sorted(stats.values(), key=lambda x: x["habit_name"])


def update_activity(
    db: Session,
    activity_id,
    *,
    activity_name: str | None = None,
    start_at: datetime | None = None,
    deadline_at: datetime | None = None,
    reminder_offsets_minutes: list[int] | None = None,
) -> Activity | None:
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        return None

    schedule_changed = False

    if activity_name is not None:
        item.activity_name = activity_name
    if start_at is not None:
        item.start_at = start_at
        schedule_changed = True
    if deadline_at is not None:
        item.deadline_at = deadline_at
        schedule_changed = True
    if reminder_offsets_minutes is not None:
        item.reminder_offsets_minutes = reminder_offsets_minutes
        schedule_changed = True

    db.commit()
    db.refresh(item)

    if schedule_changed:
        from app.repositories import reminder_schedule_repo
        reminder_schedule_repo.replace_future_pending_schedule_for_activity(
            db, item, now=datetime.now(timezone.utc)
        )

    return item


def delete_activity(db: Session, activity_id) -> bool:
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        return False
    item.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def list_completions(db: Session) -> list[Activity]:
    """All activities (including soft-deleted) that have a completed_at — used for heatmap."""
    return (
        db.query(Activity)
        .filter(Activity.completed_at.isnot(None))
        .order_by(Activity.completed_at.desc())
        .all()
    )


def list_activities(db: Session) -> list[Activity]:
    return (
        db.query(Activity)
        .filter(Activity.deleted_at.is_(None))
        .order_by(Activity.created_at.desc())
        .all()
    )


def create_activity(
    db: Session,
    *,
    activity_name: str,
    activity_kind: str,
    start_at: datetime | None = None,
    deadline_at: datetime,
    reminder_offsets_minutes: list[int] | None = None,
) -> Activity:
    item = Activity(
        activity_name=activity_name,
        activity_kind=activity_kind,
        start_at=start_at,
        deadline_at=deadline_at,
        reminder_offsets_minutes=reminder_offsets_minutes,
        status="pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_due_pending_activities(db: Session, now: datetime) -> list[Activity]:
    return (
        db.query(Activity)
        .filter(Activity.status == "pending")
        .filter(Activity.deadline_at.isnot(None))
        .filter(Activity.deadline_at <= now)
        .all()
    )


def update_status(db: Session, activity_id, status: str) -> Activity | None:
    item = db.query(Activity).filter(Activity.id == activity_id).first()
    if not item:
        return None
    item.status = status
    if status == "done":
        item.completed_at = datetime.now(timezone.utc)
    elif status in {"pending", "reschedule", "failed"}:
        item.completed_at = None
    db.commit()
    db.refresh(item)
    return item


def get_progress_summary(db: Session, *, start: datetime, end: datetime) -> dict:
    total_planned = (
        db.query(func.count(Activity.id))
        .filter(Activity.created_at >= start)
        .filter(Activity.created_at < end)
        .scalar()
        or 0
    )

    total_completed = (
        db.query(func.count(Activity.id))
        .filter(Activity.completed_at.isnot(None))
        .filter(Activity.completed_at >= start)
        .filter(Activity.completed_at < end)
        .scalar()
        or 0
    )

    habits_total = (
        db.query(func.count(Activity.id))
        .filter(Activity.activity_kind == "habit")
        .filter(Activity.created_at >= start)
        .filter(Activity.created_at < end)
        .scalar()
        or 0
    )

    habits_completed = (
        db.query(func.count(Activity.id))
        .filter(Activity.activity_kind == "habit")
        .filter(Activity.completed_at.isnot(None))
        .filter(Activity.completed_at >= start)
        .filter(Activity.completed_at < end)
        .scalar()
        or 0
    )

    reminders_total = (
        db.query(func.count(Activity.id))
        .filter(Activity.activity_kind == "reminder")
        .filter(Activity.created_at >= start)
        .filter(Activity.created_at < end)
        .scalar()
        or 0
    )

    reminders_completed = (
        db.query(func.count(Activity.id))
        .filter(Activity.activity_kind == "reminder")
        .filter(Activity.completed_at.isnot(None))
        .filter(Activity.completed_at >= start)
        .filter(Activity.completed_at < end)
        .scalar()
        or 0
    )

    completion_rate = round((total_completed / total_planned), 4) if total_planned else 0.0

    return {
        "period_start": start,
        "period_end": end,
        "total_planned": int(total_planned),
        "total_completed": int(total_completed),
        "habits": {"completed": int(habits_completed), "total": int(habits_total)},
        "reminders": {
            "completed": int(reminders_completed),
            "total": int(reminders_total),
        },
        "completion_rate": completion_rate,
    }