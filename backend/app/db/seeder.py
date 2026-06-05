from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Literal


ActivityKind = Literal["habit", "reminder"]
ActivityStatus = Literal["pending", "done", "missed"]
HabitLogIntent = Literal["done", "missed"]


@dataclass(frozen=True)
class ActivitySeed:
    name: str
    kind: ActivityKind
    deadline_at: datetime
    offsets: list[int]
    status: ActivityStatus = "pending"
    start_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True)
class HabitLogSeed:
    activity_name: str
    intent: HabitLogIntent
    created_at: datetime
    message: str


def _at(day: datetime, value: time) -> datetime:
    return day.replace(
        hour=value.hour,
        minute=value.minute,
        second=value.second,
        microsecond=0,
    )


def _today() -> datetime:
    return datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _build_activity_seeds(today: datetime) -> list[ActivitySeed]:
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    tomorrow = today + timedelta(days=1)

    return [
        ActivitySeed(
            name="Morning workout",
            kind="habit",
            start_at=_at(today, time(6, 30)),
            deadline_at=_at(today, time(8, 0)),
            offsets=[30, 10],
        ),
        ActivitySeed(
            name="Read 20 pages",
            kind="habit",
            start_at=_at(today, time(20, 0)),
            deadline_at=_at(today, time(22, 0)),
            offsets=[60, 15],
        ),
        ActivitySeed(
            name="Plan tomorrow",
            kind="habit",
            start_at=_at(today, time(21, 0)),
            deadline_at=_at(today, time(22, 30)),
            offsets=[30],
        ),
        ActivitySeed(
            name="Deep work session",
            kind="reminder",
            deadline_at=_at(today, time(11, 30)),
            offsets=[45, 15],
            status="done",
            completed_at=_at(today, time(11, 20)),
        ),
        ActivitySeed(
            name="Submit daily report",
            kind="reminder",
            deadline_at=_at(today, time(17, 30)),
            offsets=[60, 15],
        ),
        ActivitySeed(
            name="Clean workspace",
            kind="reminder",
            deadline_at=_at(today, time(19, 0)),
            offsets=[30],
        ),
        ActivitySeed(
            name="Pay internet bill",
            kind="reminder",
            deadline_at=_at(tomorrow, time(10, 0)),
            offsets=[120, 30],
        ),
        ActivitySeed(
            name="Call project mentor",
            kind="reminder",
            deadline_at=_at(tomorrow, time(15, 0)),
            offsets=[60, 10],
        ),
        ActivitySeed(
            name="Archive finished notes",
            kind="reminder",
            deadline_at=_at(yesterday, time(16, 0)),
            offsets=[30],
            status="done",
            completed_at=_at(yesterday, time(15, 35)),
        ),
        ActivitySeed(
            name="Send meeting recap",
            kind="reminder",
            deadline_at=_at(two_days_ago, time(13, 0)),
            offsets=[30],
            status="done",
            completed_at=_at(two_days_ago, time(13, 10)),
        ),
    ]


def _build_habit_log_seeds(today: datetime) -> list[HabitLogSeed]:
    templates: list[tuple[str, HabitLogIntent, int, time]] = [
        ("Morning workout", "done", 0, time(7, 15)),
        ("Read 20 pages", "done", 0, time(21, 30)),
        ("Morning workout", "done", 1, time(7, 5)),
        ("Read 20 pages", "missed", 1, time(22, 5)),
        ("Plan tomorrow", "done", 1, time(21, 45)),
        ("Morning workout", "missed", 2, time(8, 5)),
        ("Read 20 pages", "done", 2, time(21, 10)),
        ("Plan tomorrow", "done", 2, time(21, 50)),
        ("Morning workout", "done", 3, time(7, 20)),
        ("Read 20 pages", "done", 3, time(21, 40)),
        ("Morning workout", "done", 5, time(7, 10)),
        ("Plan tomorrow", "missed", 5, time(22, 40)),
        ("Read 20 pages", "done", 8, time(21, 15)),
        ("Morning workout", "done", 13, time(7, 30)),
        ("Plan tomorrow", "done", 21, time(21, 20)),
        ("Read 20 pages", "done", 34, time(21, 25)),
    ]

    seeds: list[HabitLogSeed] = []
    for activity_name, intent, days_ago, value in templates:
        created_at = _at(today - timedelta(days=days_ago), value)
        seeds.append(
            HabitLogSeed(
                activity_name=activity_name,
                intent=intent,
                created_at=created_at,
                message=f"Seeded habit occurrence marked {intent}.",
            )
        )

    return seeds


def seed_example_data() -> None:
    from app.db.base import SessionLocal
    from app.models import Activity, ActivityLog, ReminderSchedule
    from app.repositories import reminder_schedule_repo

    today = _today()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    activity_seeds = _build_activity_seeds(today)
    habit_log_seeds = _build_habit_log_seeds(today)

    db = SessionLocal()
    try:
        activities_by_name: dict[str, Activity] = {}
        created_activities = 0
        updated_activities = 0
        created_logs = 0

        for seed in activity_seeds:
            activity = (
                db.query(Activity)
                .filter(Activity.activity_name == seed.name)
                .filter(Activity.deleted_at.is_(None))
                .first()
            )

            if activity is None:
                activity = Activity(
                    activity_name=seed.name,
                    activity_kind=seed.kind,
                    start_at=seed.start_at,
                    deadline_at=seed.deadline_at,
                    reminder_offsets_minutes=seed.offsets,
                    status=seed.status,
                    completed_at=seed.completed_at,
                    created_at=min(seed.start_at or seed.deadline_at, seed.deadline_at),
                )
                db.add(activity)
                db.commit()
                db.refresh(activity)
                created_activities += 1
            else:
                activity.activity_kind = seed.kind
                activity.start_at = seed.start_at
                activity.deadline_at = seed.deadline_at
                activity.reminder_offsets_minutes = seed.offsets
                activity.status = seed.status
                activity.completed_at = seed.completed_at
                db.commit()
                db.refresh(activity)
                updated_activities += 1

            if seed.status == "pending":
                reminder_schedule_repo.replace_future_pending_schedule_for_activity(
                    db,
                    activity,
                    now=now,
                )
            else:
                (
                    db.query(ReminderSchedule)
                    .filter(ReminderSchedule.activity_id == activity.id)
                    .filter(ReminderSchedule.status == "pending")
                    .delete(synchronize_session=False)
                )
                db.commit()
            activities_by_name[seed.name] = activity

        for seed in habit_log_seeds:
            activity = activities_by_name.get(seed.activity_name)
            if activity is None:
                continue

            existing_log = (
                db.query(ActivityLog)
                .filter(ActivityLog.activity_id == activity.id)
                .filter(ActivityLog.created_at == seed.created_at)
                .filter(ActivityLog.intent_nlp["intent"].astext == seed.intent)
                .first()
            )
            if existing_log is not None:
                continue

            db.add(
                ActivityLog(
                    activity_id=activity.id,
                    bot_message=seed.message,
                    intent_nlp={"intent": seed.intent, "source": "seed"},
                    created_at=seed.created_at,
                )
            )
            created_logs += 1

        db.commit()

        print(
            "Seeded dashboard data: "
            f"{created_activities} created activities, "
            f"{updated_activities} updated activities, "
            f"{created_logs} created completion logs."
        )
    finally:
        db.close()
