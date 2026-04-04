from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import activity_repo
from app.repositories import reminder_schedule_repo
from app.schemas.activity import ActivityCreate


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


def get_progress_summary(db: Session, *, start: datetime, end: datetime) -> dict:
    return activity_repo.get_progress_summary(db, start=start, end=end)


def get_today_progress_summary(db: Session) -> dict:
    tz = ZoneInfo(settings.SCHEDULER_TIMEZONE)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return activity_repo.get_progress_summary(db, start=start, end=end)