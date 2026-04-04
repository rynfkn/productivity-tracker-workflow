from typing import Any, TypedDict

class ProductivityState(TypedDict, total=False):
    activity_id: str
    chat_id: str

    bot_message: str
    user_response: str

    intent_nlp: dict[str, Any]
    status: str

    error: str