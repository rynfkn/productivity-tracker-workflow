from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Activity


def list_activities(db: Session) -> list[Activity]:
    return db.query(Activity).order_by(Activity.created_at.desc()).all()


def create_activity(
    db: Session,
    *,
    activity_name: str,
    activity_type: str,
    activity_deadline: datetime | None = None,
    time_span: dict | None = None,
) -> Activity:
    item = Activity(
        activity_name=activity_name,
        activity_type=activity_type,
        activity_deadline=activity_deadline,
        time_span=time_span,
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
        .filter(Activity.activity_deadline.isnot(None))
        .filter(Activity.activity_deadline <= now)
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