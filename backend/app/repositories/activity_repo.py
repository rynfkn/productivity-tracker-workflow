from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Activity


def list_activities(db: Session) -> list[Activity]:
    return db.query(Activity).order_by(Activity.created_at.desc()).all()


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