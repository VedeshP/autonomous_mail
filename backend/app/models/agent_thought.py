# backend/app/models/agent_thought.py
import uuid
from sqlalchemy import Column, Integer, Text, ForeignKey, String, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

class AgentThought(Base):
    __tablename__ = "agent_thoughts"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    # Each thought belongs to a specific step (ActionLog) in a task
    action_log_id = Column(PG_UUID(as_uuid=True), ForeignKey("action_logs.id"), nullable=False, index=True, default=uuid.uuid4)
    
    # The actual "chain of thought" text
    thought_process = Column(Text, nullable=False, comment="The reasoning or observation made by the agent at this step.")
    
    # The tool used to generate this thought/observation, if any
    tool_used = Column(String, nullable=True, comment="e.g., 'search_emails', 'query_user_memory'")
    
    # --- Relationship ---
    action_log = relationship("ActionLog", back_populates="thoughts")