# backend/app/models/oauth_token.py
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, UUID, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # --- Token Fields ---
    # These are encrypted before being stored in the DB
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True) # Not always provided, but crucial to store
    expires_at = Column(DateTime, nullable=False)
    
    # The full scope of permissions granted by the user
    scopes = Column(Text, nullable=True) 
    pkce_verifier = Column(String, nullable=True, comment="Temporary storage for OAuth PKCE handshake")

    # --- Relationship ---
    user = relationship("User", back_populates="oauth_token")