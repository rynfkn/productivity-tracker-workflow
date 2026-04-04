from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Activity, ReminderSchedule


def _build_schedule_points(activity: Activity) -> list[tuple[datetime, str]]:
    points: set[tuple[datetime, str]] = set()

    if activity.activity_kind == "habit" and activity.start_at is not None:
        points.add((activity.start_at, "start"))

    if activity.deadline_at is not None:
        offsets = activity.reminder_offsets_minutes or [30]
        for minute in offsets:
            points.add((activity.deadline_at - timedelta(minutes=int(minute)), "before_deadline"))

    return sorted(points, key=lambda item: item[0])


def create_schedule_for_activity(
    db: Session,
    activity: Activity,
    *,
    min_remind_at: datetime | None = None,
) -> list[ReminderSchedule]:
    schedule_points = _build_schedule_points(activity)
    if min_remind_at is not None:
        schedule_points = [
            point for point in schedule_points if point[0] >= min_remind_at
        ]
    if not schedule_points:
        return []

    existing = (
        db.query(ReminderSchedule)
        .filter(ReminderSchedule.activity_id == activity.id)
        .all()
    )
    existing_keys = {(row.remind_at, row.reminder_kind) for row in existing}

    created: list[ReminderSchedule] = []
    for remind_at, reminder_kind in schedule_points:
        if (remind_at, reminder_kind) in existing_keys:
            continue
        row = ReminderSchedule(
            activity_id=activity.id,
            remind_at=remind_at,
            reminder_kind=reminder_kind,
            status="pending",
        )
        db.add(row)
        created.append(row)

    db.commit()
    for row in created:
        db.refresh(row)
    return created


def replace_future_pending_schedule_for_activity(
    db: Session,
    activity: Activity,
    *,
    now: datetime,
) -> list[ReminderSchedule]:
    (
        db.query(ReminderSchedule)
        .filter(ReminderSchedule.activity_id == activity.id)
        .filter(ReminderSchedule.status == "pending")
        .filter(ReminderSchedule.remind_at >= now)
        .delete(synchronize_session=False)
    )
    db.commit()
    return create_schedule_for_activity(db, activity, min_remind_at=now)


def get_due_pending_reminders(db: Session, now: datetime) -> list[ReminderSchedule]:
    return (
        db.query(ReminderSchedule)
        .filter(ReminderSchedule.status == "pending")
        .filter(ReminderSchedule.remind_at <= now)
        .order_by(ReminderSchedule.remind_at.asc())
        .all()
    )


def mark_sent(db: Session, schedule_id) -> ReminderSchedule | None:
    row = db.query(ReminderSchedule).filter(ReminderSchedule.id == schedule_id).first()
    if not row:
        return None
    row.status = "sent"
    row.sent_at = datetime.utcnow()
    row.error_message = None
    db.commit()
    db.refresh(row)
    return row


def mark_failed(db: Session, schedule_id, *, error_message: str) -> ReminderSchedule | None:
    row = db.query(ReminderSchedule).filter(ReminderSchedule.id == schedule_id).first()
    if not row:
        return None
    row.status = "failed"
    row.error_message = error_message[:1000]
    db.commit()
    db.refresh(row)
    return row
