import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, default=uuid.uuid4)
    
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    
    # --- Relationship ---
    user = relationship("User", back_populates="preferences")