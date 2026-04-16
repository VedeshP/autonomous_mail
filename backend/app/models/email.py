#backend/app/models/email.py
# Update your existing email.py file
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ARRAY, Boolean, ForeignKey, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    # This is the foreign key linking to the users table
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, default=uuid.uuid4)

    gmail_id = Column(String, unique=True, index=True, nullable=False)
    thread_id = Column(String, index=True, nullable=False)
    
    sender = Column(String, index=True, nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    
    date_received = Column(DateTime(timezone=True), index=True, nullable=False)
    labels = Column(ARRAY(String), default=[])
    snippet = Column(String, nullable=True)

    is_processed_by_agent = Column(Boolean, default=False)
    vector_id = Column(String, nullable=True, comment="ID connecting to Qdrant")
    hdfs_path = Column(String, nullable=True, comment="Path to raw file in HDFS")

    # --- Relationship ---
    owner = relationship("User", back_populates="emails")
