# backend/app/agent/llm.py
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def get_llm():
    """Returns the configured Gemini Flash model."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in .env")
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.2, # Low temperature so it acts like a precise assistant, not a poet
        google_api_key=settings.GEMINI_API_KEY
    )