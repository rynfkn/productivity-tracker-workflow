from workflow.state import ProductivityState
from workflow.nodes._backend import get_backend_bindings


def node_update_activity(state: ProductivityState) -> ProductivityState:
    activity_id = state.get("activity_id")

    if not activity_id:
        return {"error": "activity_id is required"}

    allowed_statuses = {"pending", "done", "reschedule", "failed"}
    new_status = state.get("status")
    if new_status not in allowed_statuses:
        return {"error": f"invalid status: {new_status}"}

    bindings = get_backend_bindings()

    SessionLocal = bindings["SessionLocal"]
    ActivityModel = bindings["ActivityModel"]
    ActivityLogModel = bindings["ActivityLogModel"]

    db = SessionLocal()
    try:
        item = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
        if not item:
            return {"error": f"activity not found: {activity_id}"}

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