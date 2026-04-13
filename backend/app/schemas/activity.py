from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


class ActivityCreate(BaseModel):
    activity_name: str
    activity_kind: Literal["habit", "reminder"] = Field(
        default="reminder",
        validation_alias=AliasChoices("activity_kind", "activity_type"),
    )
    start_at: datetime | None = None
    deadline_at: datetime = Field(
        validation_alias=AliasChoices("deadline_at", "activity_deadline")
    )
    reminder_offsets_minutes: list[int] = Field(default_factory=lambda: [30])

    @model_validator(mode="after")
    def validate_by_kind(self):
        if self.activity_kind == "habit" and self.start_at is None:
            raise ValueError("start_at is required for habit")
        return self

    @field_validator("reminder_offsets_minutes")
    @classmethod
    def validate_offsets(cls, value: list[int]) -> list[int]:
        cleaned = sorted(set(value))
        if not cleaned:
            raise ValueError("reminder_offsets_minutes cannot be empty")
        if any(v < 0 for v in cleaned):
            raise ValueError("reminder_offsets_minutes must be >= 0")
        return cleaned


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_name: str
    activity_kind: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    start_at: datetime | None = None
    deadline_at: datetime | None = None
    reminder_offsets_minutes: list[int] | None = None


class ActivityStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|done|failed|reschedule|missed)$")


class ActivityUpdate(BaseModel):
    activity_name: str | None = None
    start_at: datetime | None = None
    deadline_at: datetime | None = None
    reminder_offsets_minutes: list[int] | None = None

    @field_validator("reminder_offsets_minutes")
    @classmethod
    def validate_offsets(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        cleaned = sorted(set(value))
        if not cleaned:
            raise ValueError("reminder_offsets_minutes cannot be empty")
        if any(v < 0 for v in cleaned):
            raise ValueError("reminder_offsets_minutes must be >= 0")
        return cleaned


class HabitProgressItem(BaseModel):
    habit_name: str
    done: int
    missed: int
    total: int


class ProgressBucket(BaseModel):
    completed: int
    total: int


class ProgressSummaryResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_planned: int
    total_completed: int
    habits: ProgressBucket
    reminders: ProgressBucket
    completion_rate: float