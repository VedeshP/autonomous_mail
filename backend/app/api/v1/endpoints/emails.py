from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.email import Email
from app.models.user import User
from app.schemas.email import EmailResponse, LabelCreate, EmailLabelUpdate
from app.api.deps import get_current_user, get_db
from app.core.gmail_service import get_gmail_service, list_gmail_labels, create_gmail_label, modify_email_labels

router = APIRouter()

@router.get("/", response_model=List[EmailResponse])
def read_emails(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Protect the endpoint!
):
    """
    Retrieve emails belonging only to the authenticated user.
    """
    # Filter strictly by owner_id
    emails = db.query(Email)\
        .filter(Email.owner_id == current_user.id)\
        .order_by(Email.date_received.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
        
    # Safety check: SQLAlchemy might return None for the labels array,
    # but our Pydantic schema expects a list.
    for email in emails:
        if email.labels is None:
            email.labels = []
            
    return emails


@router.get("/labels")
def get_labels(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Fetch all Gmail labels for the authenticated user."""
    try:
        service = get_gmail_service(db, current_user.id)
        return list_gmail_labels(service)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/labels/create")
def create_label(
    payload: LabelCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Create a new custom label in Gmail."""
    try:
        service = get_gmail_service(db, current_user.id)
        return create_gmail_label(service, payload.name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{gmail_id}/labels")
def update_email_labels(
    gmail_id: str, 
    payload: EmailLabelUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Modify labels on an email (e.g., mark as read, archive, move to folder).
    Warning: You must pass Google's internal Label IDs (like 'UNREAD' or 'Label_4'), not the names!
    """
    try:
        service = get_gmail_service(db, current_user.id)
        return modify_email_labels(
            service, 
            gmail_id=gmail_id, 
            add_labels=payload.add_labels, 
            remove_labels=payload.remove_labels
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@router.post("/ingest/sync")
def trigger_email_ingestion(
    background_tasks: BackgroundTasks,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the Big Data pipeline.
    Fetches raw emails from Gmail and pushes them to Kafka for Spark to process.
    Returns immediately so the user isn't waiting.
    """
    # 1. Get the Gmail API client for this specific user
    try:
        service = get_gmail_service(db, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Define the background ingestion job
    def fetch_and_produce(user_id: str, fetch_limit: int):
        from app.main import kafka_producer
        
        # Ask Google for the email IDs
        results = service.users().messages().list(userId='me', maxResults=fetch_limit).execute()
        messages = results.get('messages', [])
        
        # Loop through, fetch the full raw JSON, and push to Kafka
        for msg in messages:
            raw_email = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            
            # We append the user_id so Spark knows whose database to put it in!
            raw_email["_aethermail_owner_id"] = str(user_id)
            
            # Push to the speed layer
            kafka_producer.send_raw_email("raw_emails", raw_email)

    # 3. Add to background tasks (FastAPI handles this without blocking the HTTP response)
    background_tasks.add_task(fetch_and_produce, current_user.id, limit)

    return {
        "status": "Ingestion started", 
        "message": f"Fetching {limit} emails and streaming to Kafka. Spark will process them shortly."
    }