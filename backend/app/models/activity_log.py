import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.activity import Base

class activity_log(Base):
    __tablename__ = 'activity_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID(as_uuid=True), ForeignKey('activities.id'), nullable=False)

    bot_message = Column(Text, nullable=True)
    user_message = Column(Text, nullable=True)

    intent_nlp = Column(JSONB, nullable=True) 
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    activity = relationship("activity", back_populates="logs")