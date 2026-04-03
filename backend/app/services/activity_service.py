from sqlalchemy.orm import Session

from app.repositories import activity_repo
from app.schemas.activity import ActivityCreate


def get_all_activities(db: Session):
    return activity_repo.list_activities(db)


def create_new_activity(db: Session, payload: ActivityCreate):
    return activity_repo.create_activity(
        db,
        activity_name=payload.activity_name,
        activity_type=payload.activity_type,
        activity_deadline=payload.activity_deadline,
        time_span=payload.time_span,
    )