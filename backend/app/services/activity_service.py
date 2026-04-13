from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import activity_repo
from app.repositories import reminder_schedule_repo
from app.schemas.activity import ActivityCreate, ActivityUpdate


def get_all_activities(db: Session):
    return activity_repo.list_activities(db)


def create_new_activity(db: Session, payload: ActivityCreate):
    activity = activity_repo.create_activity(
        db,
        activity_name=payload.activity_name,
        activity_kind=payload.activity_kind,
        start_at=payload.start_at,
        deadline_at=payload.deadline_at,
        reminder_offsets_minutes=payload.reminder_offsets_minutes,
    )
    reminder_schedule_repo.create_schedule_for_activity(db, activity)
    return activity


def update_existing_activity(db: Session, activity_id, payload: ActivityUpdate):
    return activity_repo.update_activity(
        db,
        activity_id,
        activity_name=payload.activity_name,
        start_at=payload.start_at,
        deadline_at=payload.deadline_at,
        reminder_offsets_minutes=payload.reminder_offsets_minutes,
    )


def delete_activity(db: Session, activity_id) -> bool:
    return activity_repo.delete_activity(db, activity_id)


def list_completions(db: Session):
    return activity_repo.list_completions(db)


def get_progress_summary(db: Session, *, start: datetime, end: datetime) -> dict:
    return activity_repo.get_progress_summary(db, start=start, end=end)


def get_today_progress_summary(db: Session) -> dict:
    tz = ZoneInfo(settings.SCHEDULER_TIMEZONE)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return activity_repo.get_progress_summary(db, start=start, end=end)


def get_habit_progress(db: Session) -> list[dict]:
    return activity_repo.get_habit_progress(db)


def mark_overdue_habits_as_missed(db: Session) -> int:
    from datetime import timezone as tz_mod
    now = datetime.now(tz_mod.utc)
    return activity_repo.mark_overdue_habits_as_missed(db, now=now)