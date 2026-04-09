import uuid
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True, default=uuid.uuid4)

    prompt = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    user = relationship("User", back_populates="agent_tasks")
    logs = relationship("ActionLog", back_populates="task", cascade="all, delete-orphan")


class ActionType(enum.Enum):
    LABEL = "label"
    DELETE = "delete"
    ARCHIVE = "archive"
    DRAFT = "draft"
    SUMMARY = "summary"
    ERROR = "error"

# Updated action log
class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id = Column(PG_UUID(as_uuid=True), ForeignKey("agent_tasks.id"), nullable=False, index=True, default=uuid.uuid4)

    action_type = Column(Enum(ActionType), nullable=False)
    target_id = Column(String, nullable=True, comment="e.g., the gmail_id of the email")
    details = Column(Text, nullable=True, comment="e.g., 'Applied label: Important'")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    task = relationship("AgentTask", back_populates="logs")
    # Add this new relationship
    thoughts = relationship("AgentThought", back_populates="action_log", cascade="all, delete-orphan")