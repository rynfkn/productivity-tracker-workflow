from typing import Any, TypedDict

class ProductivityState(TypedDict, total=False):
    activity_id: str
    chat_id: str
    schedule_id: str
    reminder_kind: str
    activity_kind: str

    bot_message: str
    user_response: str

    intent_nlp: dict[str, Any]
    status: str
    reschedule_deadline: str

    error: str


class CommandState(TypedDict, total=False):
    chat_id: str
    user_message: str

    command_intent: str  # add_activity | delete_activity | list_activities | unknown
    parsed_activity_name: str
    parsed_activity_kind: str
    parsed_deadline_at: str
    parsed_start_at: str
    parsed_reminder_offsets_minutes: list[int]

    result_message: str
    error: str
