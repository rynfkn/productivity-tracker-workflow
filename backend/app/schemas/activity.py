from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActivityCreate(BaseModel):
    activity_name: str
    activity_type: str
    activity_deadline: datetime | None = None
    time_span: dict[str, Any] | None = None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_name: str
    activity_type: str
    status: str
    created_at: datetime
    activity_deadline: datetime | None = None
    time_span: dict[str, Any] | None = None


class ActivityStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|done|failed|reschedule)$")