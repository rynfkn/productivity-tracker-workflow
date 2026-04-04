import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.db.base import SessionLocal
from app.repositories import reminder_schedule_repo

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)


def _invoke_workflow(activity_id: str, chat_id: str) -> None:
    # Add the project root to sys.path so we can import workflow
    project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
    if project_root not in sys.path:
        sys.path.append(project_root)

    # lazy import to avoid circular/init overhead
    from workflow.graph import app as workflow_app

    logger.info("Invoking workflow activity_id=%s chat_id=%s", activity_id, chat_id)
    result = workflow_app.invoke(
        {
            "activity_id": str(activity_id),
            "chat_id": str(chat_id),
        },
        config={"configurable": {"thread_id": f"{chat_id}:{activity_id}"}},
    )
    logger.info("Workflow finished activity_id=%s result=%s", activity_id, result)



def check_and_trigger_activities() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due = reminder_schedule_repo.get_due_pending_reminders(db, now=now)
        logger.info("Scheduler tick now_utc=%s due_reminder_count=%d", now.isoformat(), len(due))
        for schedule in due:
            chat_id = settings.USER_CHAT_ID
            if not chat_id:
                logger.warning(
                    "USER_CHAT_ID is empty; skip trigger schedule_id=%s activity_id=%s",
                    schedule.id,
                    schedule.activity_id,
                )
                reminder_schedule_repo.mark_failed(
                    db,
                    schedule.id,
                    error_message="USER_CHAT_ID is empty",
                )
                continue

            if schedule.activity and schedule.activity.status != "pending":
                logger.info(
                    "Skip non-pending activity schedule_id=%s activity_id=%s activity_status=%s",
                    schedule.id,
                    schedule.activity_id,
                    schedule.activity.status,
                )
                reminder_schedule_repo.mark_failed(
                    db,
                    schedule.id,
                    error_message=f"activity status is {schedule.activity.status}",
                )
                continue

            try:
                logger.info(
                    "Trigger reminder schedule_id=%s activity_id=%s reminder_kind=%s remind_at=%s",
                    schedule.id,
                    schedule.activity_id,
                    schedule.reminder_kind,
                    schedule.remind_at,
                )
                _invoke_workflow(activity_id=str(schedule.activity_id), chat_id=chat_id)
                reminder_schedule_repo.mark_sent(db, schedule.id)
            except Exception as exc:
                logger.exception(
                    "Reminder trigger failed schedule_id=%s activity_id=%s: %s",
                    schedule.id,
                    schedule.activity_id,
                    exc,
                )
                reminder_schedule_repo.mark_failed(
                    db,
                    schedule.id,
                    error_message=str(exc),
                )
    except Exception as exc:
        logger.exception("scheduler check failed: %s", exc)
    finally:
        db.close()


def start_scheduler() -> None:
    if not settings.SCHEDULER_ENABLED:
        return
    scheduler.add_job(
        check_and_trigger_activities,
        "interval",
        seconds=settings.SCHEDULER_INTERVAL_SECONDS,
        id="check_due_reminders",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)