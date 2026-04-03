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
    activity_type = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    activity_deadline = Column(DateTime(timezone=True), nullable=True)
    time_span = Column(JSONB, nullable=True)

    logs = relationship(
        "ActivityLog", back_populates="activity", cascade="all, delete-orphan"
    )