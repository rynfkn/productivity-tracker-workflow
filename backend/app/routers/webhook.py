from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories import activity_log_repo

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()

    message = data.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    user_text = message.get("text")

    if not chat_id or not user_text:
        return {"ok": True, "message": "ignored"}

    # Continue workflow after interrupt
    from workflow.graph import app as workflow_app

    result = workflow_app.invoke(
        {"user_response": user_text, "chat_id": str(chat_id)},
        config={"configurable": {"thread_id": str(chat_id)}},
    )

    # Optional best-effort log if activity_id available in workflow output
    activity_id = result.get("activity_id") if isinstance(result, dict) else None
    if activity_id:
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