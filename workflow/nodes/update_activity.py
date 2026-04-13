from datetime import datetime, timezone

from workflow.state import ProductivityState
from workflow.nodes._backend import get_backend_bindings


def _parse_iso_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def node_update_activity(state: ProductivityState) -> ProductivityState:
    activity_id = state.get("activity_id")

    if not activity_id:
        return {"error": "activity_id is required"}

    allowed_statuses = {"pending", "done", "reschedule", "failed", "missed"}
    new_status = state.get("status")
    if new_status not in allowed_statuses:
        return {"error": f"invalid status: {new_status}"}

    bindings = get_backend_bindings()

    SessionLocal = bindings["SessionLocal"]
    ActivityModel = bindings["ActivityModel"]
    ActivityLogModel = bindings["ActivityLogModel"]

    db = SessionLocal()
    try:
        from backend.app.repositories import reminder_schedule_repo

        item = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
        if not item:
            return {"error": f"activity not found: {activity_id}"}

        if new_status == "done":
            item.status = "done"
            item.completed_at = datetime.now(timezone.utc)
        elif new_status == "reschedule":
            requested_deadline = _parse_iso_datetime(
                state.get("reschedule_deadline")
                or (state.get("intent_nlp") or {}).get("new_deadline")
            )
            if requested_deadline is None:
                return {"error": "reschedule requested but no valid new deadline was provided"}

            item.deadline_at = requested_deadline
            item.status = "pending"
            item.completed_at = None

            reminder_schedule_repo.replace_future_pending_schedule_for_activity(
                db,
                item,
                now=datetime.now(timezone.utc),
            )
        elif new_status == "missed":
            item.status = "missed"
            item.completed_at = None
        else:
            item.status = new_status

        log = ActivityLogModel(
            activity_id=item.id,
            bot_message=state.get("bot_message"),
            user_message=state.get("user_response"),
            intent_nlp=state.get("intent_nlp"),
        )
        db.add(log)
        db.commit()
        db.refresh(item)

        return {"status": item.status, "activity_id": str(item.id)}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()