import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class activity(Base):
    __tablename__ = 'activity'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_name = Column(String(255), nullable=False)
    activity_type = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    activity_deadline = Column(DateTime(timezone=True), nullable=True)
    time_start = Column(DateTime(timezone=True), nullable=True)
    time_end = Column(DateTime(timezone=True), nullable=True)

    logs = relationship("activity_log", back_populates="activity", cascade="all, delete-orphan")