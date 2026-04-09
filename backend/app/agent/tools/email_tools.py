# backend/app/agent/tools/email_tools.py
import json
import requests
from langchain_core.tools import tool
from qdrant_client import QdrantClient
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.email import Email

# Initialize Qdrant Client globally for the tools
q_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

def _get_query_embedding(text: str) -> list:
    """Helper function to turn the agent's search query into a vector using Ollama."""
    url = "http://localhost:11434/api/embeddings"
    payload = {"model": "nomic-embed-text", "prompt": text}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("embedding")

@tool
def search_emails_semantic(query: str, limit: int = 5) -> str:
    """
    Search the user's email inbox using semantic meaning. 
    Use this when the user asks to find an email about a topic, concept, or specific event.
    Returns a JSON string of the best matching emails.
    """
    try:
        # 1. Convert the agent's search query into a vector
        query_vector = _get_query_embedding(query)
        
        # 2. Search Qdrant for the closest matching emails
        search_result = q_client.query_points(
            collection_name="emails",
            query=query_vector,
            limit=limit
        ).points
        
        if not search_result:
            return "No matching emails found."

        # 3. Format the results for the LLM to read
        results_formatted = []
        for hit in search_result:
            payload = hit.payload
            results_formatted.append({
                "gmail_id": payload.get("gmail_id"),
                "sender": payload.get("sender"),
                "subject": payload.get("subject"),
                "date": payload.get("date_received"),
                "relevance_score": hit.score
            })
            
        return json.dumps(results_formatted, indent=2)
    except Exception as e:
        return f"Error searching database: {str(e)}"

# We bundle the tools into a list for LangGraph
search_tools_list = [search_emails_semantic]