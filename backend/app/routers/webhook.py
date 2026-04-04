import logging
import re

from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.repositories import activity_log_repo

router = APIRouter(prefix="/webhook", tags=["webhook"])

logger = logging.getLogger(__name__)
ACTIVITY_REF_RE = re.compile(r"Ref:\s*([0-9a-fA-F-]{36})")

@router.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    message = data.get("message") or {}
    chat = message.get("chat") or {}
    reply_to = message.get("reply_to_message") or {}

    chat_id = str(chat.get("id") or "")
    user_text = (message.get("text") or "").strip()
    reply_to_text = (reply_to.get("text") or "").strip()
    message_id = message.get("message_id")
    reply_to_message_id = reply_to.get("message_id")

    if not chat_id or not user_text:
        return {"ok": True, "message": "ignored"}

    match = ACTIVITY_REF_RE.search(reply_to_text) or ACTIVITY_REF_RE.search(user_text)
    if not match:
        logger.info(
            "telegram_webhook ignored chat_id=%s message_id=%s reason=no_activity_ref",
            chat_id,
            message_id,
        )
        return {"ok": True, "message": "ignored: no activity ref"}

    activity_id = match.group(1)

    logger.info(
        "telegram_webhook received chat_id=%s message_id=%s reply_to_message_id=%s activity_id=%s text=%r",
        chat_id,
        message_id,
        reply_to_message_id,
        activity_id,
        user_text,
    )

    # Continue workflow after interrupt
    from workflow.graph import app as workflow_app

    result = workflow_app.invoke(
        {
            "activity_id": str(activity_id),
            "chat_id": str(chat_id),
            "user_response": user_text,
        },
        config={"configurable": {"thread_id": f"{chat_id}:{activity_id}"}},
    )

    if isinstance(result, dict):
        logger.info("telegram_webhook workflow_result activity_id=%s result=%s", activity_id, result)

    # Optional best-effort log
    if activity_id and isinstance(result, dict):
        db: Session = SessionLocal()
        try:
            activity_log_repo.create_log(
                db,
                activity_id=activity_id,
                user_message=user_text,
                intent_nlp=result.get("intent_nlp"),
            )
        finally:
            db.close()

    return {"ok": True}