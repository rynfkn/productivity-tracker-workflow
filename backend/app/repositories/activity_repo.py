from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Activity, ActivityLog


HABIT_TERMINAL_INTENTS = {"done", "missed"}


def _intent_from_log(log: ActivityLog) -> str | None:
    if not isinstance(log.intent_nlp, dict):
        return None
    intent = log.intent_nlp.get("intent")
    return intent if intent in HABIT_TERMINAL_INTENTS else None


def _is_countable_habit_log(log: ActivityLog) -> bool:
    if not isinstance(log.intent_nlp, dict):
        return False
    source = log.intent_nlp.get("source")
    return log.bot_message is not None or source in {"api", "scheduler"}


def advance_habit_to_next_occurrence(activity: Activity, now: datetime) -> None:
    """Move a daily habit window forward so the same habit can notify again."""
    if activity.activity_kind != "habit":
        return

    days = 1
    if activity.deadline_at is not None:
        next_deadline = activity.deadline_at + timedelta(days=days)
        while next_deadline <= now:
            days += 1
            next_deadline = activity.deadline_at + timedelta(days=days)

    if activity.start_at is not None:
        activity.start_at = activity.start_at + timedelta(days=days)
    if activity.deadline_at is not None:
        activity.deadline_at = activity.deadline_at + timedelta(days=days)


def mark_overdue_habits_as_missed(db: Session, now: datetime) -> int:
    """Record missed habit occurrences and move them to their next daily window.
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
        row.status = "pending"
        row.completed_at = None
        db.add(
            ActivityLog(
                activity_id=row.id,
                bot_message="Habit deadline passed without completion.",
                intent_nlp={"intent": "missed", "source": "scheduler"},
            )
        )
        advance_habit_to_next_occurrence(row, now)
    db.commit()

    if rows:
        from app.repositories import reminder_schedule_repo

        for row in rows:
            reminder_schedule_repo.mark_past_pending_schedule_for_activity(
                db,
                row,
                now=now,
                error_message="habit occurrence was marked missed",
            )
            reminder_schedule_repo.replace_future_pending_schedule_for_activity(
                db, row, now=now
            )

    return len(rows)


def reactivate_terminal_habits(db: Session, now: datetime) -> int:
    """Reactivate habits completed before recurring habit support existed."""
    rows = (
        db.query(Activity)
        .filter(Activity.activity_kind == "habit")
        .filter(Activity.deleted_at.is_(None))
        .filter(Activity.status.in_(["done", "missed"]))
        .all()
    )
    for row in rows:
        previous_status = row.status
        existing_logs = (
            db.query(ActivityLog)
            .filter(ActivityLog.activity_id == row.id)
            .all()
        )
        if previous_status == "done" and row.completed_at is not None:
            has_completion_log = any(
                _is_countable_habit_log(log) and _intent_from_log(log) == "done"
                for log in existing_logs
            )
            if not has_completion_log:
                db.add(
                    ActivityLog(
                        activity_id=row.id,
                        bot_message="Backfilled completion before habit recurrence.",
                        intent_nlp={"intent": "done", "source": "migration"},
                        created_at=row.completed_at,
                    )
                )
        if previous_status == "missed":
            has_missed_log = any(
                _is_countable_habit_log(log) and _intent_from_log(log) == "missed"
                for log in existing_logs
            )
            if not has_missed_log:
                db.add(
                    ActivityLog(
                        activity_id=row.id,
                        bot_message="Backfilled missed habit before recurrence.",
                        intent_nlp={"intent": "missed", "source": "migration"},
                        created_at=row.deadline_at or now,
                    )
                )
            row.completed_at = None
        row.status = "pending"
        advance_habit_to_next_occurrence(row, now)

    db.commit()

    if rows:
        from app.repositories import reminder_schedule_repo

        for row in rows:
            reminder_schedule_repo.mark_past_pending_schedule_for_activity(
                db,
                row,
                now=now,
                error_message="habit was reactivated for recurrence",
            )
            reminder_schedule_repo.replace_future_pending_schedule_for_activity(
                db, row, now=now
            )

    return len(rows)


def get_habit_progress(db: Session) -> list[dict]:
    """Return per-habit-name progress: total occurrences, done, missed (up to now)."""
    rows = (
        db.query(ActivityLog, Activity)
        .join(Activity, ActivityLog.activity_id == Activity.id)
        .filter(Activity.activity_kind == "habit")
        .all()
    )

    stats: dict[str, dict] = {}
    for log, activity in rows:
        if not _is_countable_habit_log(log):
            continue
        intent = _intent_from_log(log)
        if intent is None:
            continue

        name = activity.activity_name
        if name not in stats:
            stats[name] = {"habit_name": name, "done": 0, "missed": 0, "total": 0}
        stats[name][intent] += 1
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


def list_completions(db: Session) -> list[dict]:
    """All activities (including soft-deleted) that have a completed_at — used for heatmap."""
    reminder_rows = (
        db.query(Activity)
        .filter(Activity.activity_kind != "habit")
        .filter(Activity.completed_at.isnot(None))
        .all()
    )

    completions = [
        {
            "id": row.id,
            "activity_name": row.activity_name,
            "activity_kind": row.activity_kind,
            "status": row.status,
            "created_at": row.created_at,
            "completed_at": row.completed_at,
            "start_at": row.start_at,
            "deadline_at": row.deadline_at,
            "reminder_offsets_minutes": row.reminder_offsets_minutes,
        }
        for row in reminder_rows
    ]

    habit_rows = (
        db.query(ActivityLog, Activity)
        .join(Activity, ActivityLog.activity_id == Activity.id)
        .filter(Activity.activity_kind == "habit")
        .all()
    )

    for log, activity in habit_rows:
        if not _is_countable_habit_log(log):
            continue
        if _intent_from_log(log) != "done":
            continue
        completions.append(
            {
                "id": log.id,
                "activity_name": activity.activity_name,
                "activity_kind": activity.activity_kind,
                "status": "done",
                "created_at": activity.created_at,
                "completed_at": log.created_at,
                "start_at": activity.start_at,
                "deadline_at": activity.deadline_at,
                "reminder_offsets_minutes": activity.reminder_offsets_minutes,
            }
        )

    return sorted(completions, key=lambda item: item["completed_at"], reverse=True)


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
    now = datetime.now(timezone.utc)

    if item.activity_kind == "habit" and status in HABIT_TERMINAL_INTENTS:
        item.status = "pending"
        item.completed_at = now if status == "done" else None
        db.add(
            ActivityLog(
                activity_id=item.id,
                intent_nlp={"intent": status, "source": "api"},
            )
        )
        advance_habit_to_next_occurrence(item, now)
        db.commit()
        db.refresh(item)

        from app.repositories import reminder_schedule_repo

        reminder_schedule_repo.replace_future_pending_schedule_for_activity(
            db, item, now=now
        )
        return item

    item.status = status
    if status == "done":
        item.completed_at = now
    elif status in {"pending", "reschedule", "failed"}:
        item.completed_at = None
    db.commit()
    db.refresh(item)
    return item


def get_progress_summary(db: Session, *, start: datetime, end: datetime) -> dict:
    habit_logs = (
        db.query(ActivityLog, Activity)
        .join(Activity, ActivityLog.activity_id == Activity.id)
        .filter(Activity.activity_kind == "habit")
        .filter(ActivityLog.created_at >= start)
        .filter(ActivityLog.created_at < end)
        .all()
    )

    habit_ids = {
        row.id
        for row in db.query(Activity.id)
        .filter(Activity.activity_kind == "habit")
        .filter(Activity.deadline_at.isnot(None))
        .filter(Activity.deadline_at >= start)
        .filter(Activity.deadline_at < end)
        .all()
    }

    habits_completed = sum(
        1
        for log, _activity in habit_logs
        if _is_countable_habit_log(log) and _intent_from_log(log) == "done"
    )
    for log, activity in habit_logs:
        if (
            _is_countable_habit_log(log)
            and _intent_from_log(log) in HABIT_TERMINAL_INTENTS
        ):
            habit_ids.add(activity.id)

    habits_total = len(habit_ids)

    reminders_completed = (
        db.query(func.count(Activity.id))
        .filter(Activity.activity_kind != "habit")
        .filter(Activity.completed_at.isnot(None))
        .filter(Activity.completed_at >= start)
        .filter(Activity.completed_at < end)
        .scalar()
        or 0
    )

    reminders_total = (
        db.query(func.count(Activity.id))
        .filter(Activity.activity_kind == "reminder")
        .filter(Activity.deadline_at.isnot(None))
        .filter(Activity.deadline_at >= start)
        .filter(Activity.deadline_at < end)
        .scalar()
        or 0
    )

    total_planned = reminders_total + habits_total
    total_completed = reminders_completed + habits_completed

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
