from sqlalchemy.orm import Session

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