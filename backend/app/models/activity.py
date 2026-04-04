import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_name = Column(String(255), nullable=False)
    activity_kind = Column(String(20), nullable=False, default="reminder")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    start_at = Column(DateTime(timezone=True), nullable=True)
    deadline_at = Column(DateTime(timezone=True), nullable=True)
    reminder_offsets_minutes = Column(JSONB, nullable=True)

    logs = relationship(
        "ActivityLog", back_populates="activity", cascade="all, delete-orphan"
    )
    reminder_schedules = relationship(
        "ReminderSchedule", back_populates="activity", cascade="all, delete-orphan"
    )