from sqlalchemy.orm import Session

from app.models import ActivityLog


def create_log(
    db: Session,
    *,
    activity_id,
    bot_message: str | None = None,
    user_message: str | None = None,
    intent_nlp: dict | None = None,
) -> ActivityLog:
    row = ActivityLog(
        activity_id=activity_id,
        bot_message=bot_message,
        user_message=user_message,
        intent_nlp=intent_nlp,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row