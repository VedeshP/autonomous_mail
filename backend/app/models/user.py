# backend/app/models/user.py
import uuid
from sqlalchemy import Column, Integer, String, Boolean, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    
    # --- Google OAuth Specific Fields ---
    google_sub = Column(String, unique=True, index=True, nullable=False, comment="Google's unique user ID (the 'sub' claim)")
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    picture_url = Column(String, nullable=True) # URL to the user's Google profile picture
    
    # --- Application Specific Fields ---
    is_active = Column(Boolean(), default=True)

    # --- Relationships ---
    emails = relationship("Email", back_populates="owner")
    agent_tasks = relationship("AgentTask", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user")
    
    # This is a one-to-one relationship to the OAuth tokens
    oauth_token = relationship("OAuthToken", back_populates="user", uselist=False, cascade="all, delete-orphan")