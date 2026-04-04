import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ReminderSchedule(Base):
    __tablename__ = "reminder_schedules"
    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "remind_at",
            "reminder_kind",
            name="uq_reminder_schedule_activity_time_kind",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id"), nullable=False)

    remind_at = Column(DateTime(timezone=True), nullable=False)
    reminder_kind = Column(String(32), nullable=False)  # start | before_deadline
    status = Column(String(20), nullable=False, default="pending")

    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    activity = relationship("Activity", back_populates="reminder_schedules")
