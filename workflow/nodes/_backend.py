from __future__ import annotations

from typing import Any


def get_backend_bindings() -> dict[str, Any]:
    # New backend structure
    try:
        from backend.app.db.base import SessionLocal
        from backend.app.models import Activity, ActivityLog

        return {
            "SessionLocal": SessionLocal,
            "ActivityModel": Activity,
            "ActivityLogModel": ActivityLog,
            "deadline_field": "activity_deadline",
        }
    except Exception:
        pass

    # Legacy backend structure
    from backend.database import SessionLocal  # type: ignore
    from backend.models import activity, activity_log  # type: ignore

    return {
        "SessionLocal": SessionLocal,
        "ActivityModel": activity,
        "ActivityLogModel": activity_log,
        "deadline_field": "activity_deadline",
    }