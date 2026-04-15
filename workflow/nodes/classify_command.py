import os
from datetime import datetime
from zoneinfo import ZoneInfo

from workflow.services.llm_service import parse_command
from workflow.state import CommandState


def node_classify_command(state: CommandState) -> CommandState:
    user_message = state.get("user_message", "")
    timezone = os.getenv("SCHEDULER_TIMEZONE", "Asia/Jakarta")
    now = datetime.now(ZoneInfo(timezone))
    current_datetime = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    result = parse_command(user_message, current_datetime, timezone)

    return {
        "command_intent": result.get("intent", "unknown"),
        "parsed_activity_name": result.get("activity_name"),
        "parsed_activity_kind": result.get("activity_kind", "reminder"),
        "parsed_deadline_at": result.get("deadline_at"),
        "parsed_start_at": result.get("start_at"),
        "parsed_reminder_offsets_minutes": result.get("reminder_offsets_minutes") or [30],
    }
