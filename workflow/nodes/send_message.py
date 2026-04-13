import os

import requests

from workflow.nodes._backend import get_backend_bindings
from workflow.state import ProductivityState

import dotenv

dotenv.load_dotenv()

def node_send_message(state: ProductivityState) -> ProductivityState:
    if state.get("bot_message") or state.get("user_response"):
        return {}

    chat_id = state.get("chat_id")
    activity_id = state.get("activity_id")
    if not chat_id or not activity_id:
        return {"error": "chat_id/activity_id is required"}

    bindings = get_backend_bindings()
    SessionLocal = bindings["SessionLocal"]
    ActivityModel = bindings["ActivityModel"]

    db = SessionLocal()
    try:
        item = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
        if not item:
            return {"error": f"activity not found: {activity_id}"}

        if item.activity_kind == "habit":
            msg = (
                f"Habit check-in:\n"
                f"- Habit: {item.activity_name}\n\n"
                f"Did you complete this habit today? Reply yes or no.\n"
                f"Ref: {item.id}"
            )
        else:
            msg = (
                f"Activity reminder:\n"
                f"- Name: {item.activity_name}\n"
                f"- Type: {item.activity_kind}\n\n"
                f"Has this activity been completed? You can reply done, reschedule, or failed.\n"
                f"Ref: {item.id}"
            )

        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token:
            return {"error": "TELEGRAM_BOT_TOKEN not configured", "bot_message": msg}

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": str(chat_id), "text": msg}, timeout=20)
        r.raise_for_status()

        payload = r.json()
        if not payload.get("ok"):
            return {"error": f"Telegram API error: {payload}", "bot_message": msg}


        return {"bot_message": msg, "activity_kind": item.activity_kind}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()