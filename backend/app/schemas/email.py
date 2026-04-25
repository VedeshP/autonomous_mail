#backend/app/schemas/email.py
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class EmailBase(BaseModel):
    gmail_id: str = Field(..., description="The unique ID from Gmail")
    thread_id: str = Field(..., description="The thread ID to group conversations")
    sender: str = Field(..., description="The From header")
    recipient: str = Field(..., description="The To header")
    subject: str = Field(..., description="The Subject header")
    date_received: datetime = Field(..., description="Parsed from internalDate")
    labels: Optional[List[str]] = Field(default=[], description="List of Gmail labels")
    snippet: str = Field(..., description="Short preview text")

class EmailCreate(EmailBase):
    # When creating, we also handle the raw body, but it won't go to Postgres directly
    raw_text_body: Optional[str] = Field(None, description="Decoded plain text body")
    raw_html_body: Optional[str] = Field(None, description="Decoded HTML body")

class EmailResponse(EmailBase):
    # What the API returns to the frontend
    id: UUID
    
    class Config:
        from_attributes = True
        
        
class LabelCreate(BaseModel):
    name: str = Field(..., description="The name of the new label/folder to create")

class EmailLabelUpdate(BaseModel):
    add_labels: List[str] = Field(default=[], description="List of Label IDs to add")
    remove_labels: List[str] = Field(default=[], description="List of Label IDs to remove")
