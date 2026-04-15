import os
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from workflow.nodes._backend import get_backend_bindings
from workflow.state import CommandState


def _send_message(chat_id: str, text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": str(chat_id), "text": text}, timeout=20)


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            tz = ZoneInfo(os.getenv("SCHEDULER_TIMEZONE", "Asia/Jakarta"))
            parsed = parsed.replace(tzinfo=tz)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return "N/A"
    tz = ZoneInfo(os.getenv("SCHEDULER_TIMEZONE", "Asia/Jakarta"))
    return dt.astimezone(tz).strftime("%d %b %Y %H:%M")


def node_handle_command(state: CommandState) -> CommandState:
    from backend.app.services import activity_service
    from backend.app.schemas.activity import ActivityCreate

    chat_id = state.get("chat_id", "")
    intent = state.get("command_intent", "unknown")

    bindings = get_backend_bindings()
    SessionLocal = bindings["SessionLocal"]
    db = SessionLocal()

    try:
        if intent == "add_activity":
            name = (state.get("parsed_activity_name") or "").strip()
            kind = state.get("parsed_activity_kind") or "reminder"
            deadline_str = state.get("parsed_deadline_at")
            start_str = state.get("parsed_start_at")
            offsets = state.get("parsed_reminder_offsets_minutes") or [30]

            if not name:
                msg = (
                    "I couldn't identify the activity name. Please try again.\n\n"
                    "Example:\n"
                    "  Add reminder: Buy groceries by tomorrow 6pm\n"
                    "  Add habit: Morning run daily at 7am"
                )
                _send_message(chat_id, msg)
                return {"result_message": msg}

            deadline = _parse_iso(deadline_str)
            if not deadline:
                msg = (
                    f"I couldn't parse the deadline for '{name}'. Please include a date/time.\n\n"
                    "Example: Add reminder: Buy groceries by tomorrow 6pm"
                )
                _send_message(chat_id, msg)
                return {"result_message": msg}

            start = _parse_iso(start_str) or deadline

            payload = ActivityCreate(
                activity_name=name,
                activity_kind=kind,
                deadline_at=deadline,
                start_at=start if kind == "habit" else None,
                reminder_offsets_minutes=offsets,
            )
            activity = activity_service.create_new_activity(db, payload)

            msg = (
                f"Activity added!\n\n"
                f"Name: {activity.activity_name}\n"
                f"Kind: {activity.activity_kind}\n"
                f"Deadline: {_fmt_dt(activity.deadline_at)}"
            )
            _send_message(chat_id, msg)
            return {"result_message": msg}

        elif intent == "delete_activity":
            name = (state.get("parsed_activity_name") or "").strip()
            if not name:
                msg = (
                    "Please specify the activity name to delete.\n\n"
                    "Example: Delete: Buy groceries"
                )
                _send_message(chat_id, msg)
                return {"result_message": msg}

            all_activities = activity_service.get_all_activities(db)
            matches = [a for a in all_activities if name.lower() in a.activity_name.lower()]

            if not matches:
                msg = f"No activity found matching '{name}'."
                _send_message(chat_id, msg)
                return {"result_message": msg}

            if len(matches) > 1:
                lines = [f"Multiple activities match '{name}':\n"]
                for i, a in enumerate(matches[:10]):
                    lines.append(f"{i + 1}. {a.activity_name}")
                lines.append("\nPlease be more specific.")
                msg = "\n".join(lines)
                _send_message(chat_id, msg)
                return {"result_message": msg}

            activity = matches[0]
            activity_service.delete_activity(db, activity.id)
            msg = f"Activity '{activity.activity_name}' has been deleted."
            _send_message(chat_id, msg)
            return {"result_message": msg}

        elif intent == "list_activities":
            all_activities = activity_service.get_all_activities(db)
            if not all_activities:
                msg = "You have no activities."
                _send_message(chat_id, msg)
                return {"result_message": msg}

            lines = ["Your activities:\n"]
            for i, a in enumerate(all_activities[:20]):
                deadline_label = _fmt_dt(a.deadline_at)
                lines.append(f"{i + 1}. {a.activity_name} [{a.activity_kind}] - {a.status} - {deadline_label}")

            if len(all_activities) > 20:
                lines.append(f"\n... and {len(all_activities) - 20} more")

            msg = "\n".join(lines)
            _send_message(chat_id, msg)
            return {"result_message": msg}

        else:
            msg = (
                "I didn't understand that. Here's what I can do:\n\n"
                "Add an activity:\n"
                "  Add reminder: Buy groceries by tomorrow 6pm\n"
                "  Add habit: Morning run daily at 7am\n\n"
                "Delete an activity:\n"
                "  Delete: Buy groceries\n\n"
                "List activities:\n"
                "  List activities"
            )
            _send_message(chat_id, msg)
            return {"result_message": msg}

    except Exception as e:
        error_msg = f"An error occurred: {e}"
        try:
            _send_message(chat_id, error_msg)
        except Exception:
            pass
        return {"error": str(e), "result_message": error_msg}
    finally:
        db.close()
