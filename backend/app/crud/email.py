# backend/app/crud/email.py
from sqlalchemy.orm import Session
from app.models.email import Email
from app.schemas.email import EmailCreate

def create_email(db: Session, email_in: EmailCreate, owner_id: str) -> Email:
    """
    Takes a parsed EmailCreate schema and saves it to the PostgreSQL database.
    """
    # 1. Map the Pydantic schema fields to the SQLAlchemy model
    db_email = Email(
        owner_id=owner_id,
        gmail_id=email_in.gmail_id,
        thread_id=email_in.thread_id,
        sender=email_in.sender,
        recipient=email_in.recipient,
        subject=email_in.subject,
        date_received=email_in.date_received,
        labels=email_in.labels,
        snippet=email_in.snippet,
        # We leave vector_id and hdfs_path empty for now. 
        # Spark will update these later!
    )
    
    # 2. Add to session and commit to the database
    db.add(db_email)
    db.commit()
    
    # 3. Refresh to get the generated UUID primary key
    db.refresh(db_email)
    
    return db_email

def get_email_by_gmail_id(db: Session, gmail_id: str):
    return db.query(Email).filter(Email.gmail_id == gmail_id).first()