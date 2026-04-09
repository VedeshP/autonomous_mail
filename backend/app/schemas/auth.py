# backend/app/schemas/auth.py
from pydantic import BaseModel
from uuid import UUID

class GoogleToken(BaseModel):
    """The payload sent by the Frontend containing the Google ID Token"""
    token: str

class TokenResponse(BaseModel):
    """The payload we send back to the Frontend"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str