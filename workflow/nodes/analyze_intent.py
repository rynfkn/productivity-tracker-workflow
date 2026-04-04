from langgraph.types import interrupt

from workflow.services.llm_service import classify_intent
from workflow.state import ProductivityState


def node_analyze_intent(state: ProductivityState) -> ProductivityState:
    user_response = (state.get("user_response") or "").strip()

    if not user_response:
        user_response = interrupt("Waiting for user reply from Telegram webhook")

    intent = classify_intent(user_response)
    status = intent.get("intent", "failed")
    if status not in {"done", "reschedule", "failed"}:
        status = "failed"

    return {
        "user_response": user_response,
        "intent_nlp": intent,
        "status": status,
        "reschedule_deadline": intent.get("new_deadline") or "",
    }