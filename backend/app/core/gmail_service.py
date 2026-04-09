# backend/app/core/gmail_service.py
import hashlib
import base64
import os

import json
from datetime import datetime
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.config import settings
from app.models.oauth_token import OAuthToken
from app.models.user import User

# The exact permission we need to organize and draft emails (modify)
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# We build the Google Client config dynamically from our .env variables
# This saves us from needing a hardcoded client_secrets.json file in production
CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

# The URL Google will redirect to after the user clicks "Allow"
# We will create this endpoint in the next step
REDIRECT_URI = "http://localhost:8000/api/v1/auth/gmail/callback"


def generate_pkce_pair():
    """Generates a secure PKCE Code Verifier and Code Challenge."""
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')
    return verifier, challenge


def get_gmail_auth_url(db: Session, user_id: str) -> str:
    """
    Generates the Google URL WITH a PKCE challenge, and saves the verifier.
    """
    # 1. Generate the PKCE cryptographic pair
    verifier, challenge = generate_pkce_pair()

    # 2. Save the verifier to the database so the callback can find it later
    token_record = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
    if not token_record:
        token_record = OAuthToken(user_id=user_id, access_token="pending", expires_at=datetime.utcnow())
        db.add(token_record)
        
    token_record.pkce_verifier = verifier
    db.commit()

    # 3. Create the Google Flow
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    # 4. Generate the URL, manually injecting the PKCE challenge
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        state=str(user_id),
        code_challenge=challenge,
        code_challenge_method='S256'
    )
    return authorization_url

def exchange_code_and_save_tokens(db: Session, code: str, user_id: str):
    """
    Swaps the code for tokens using the stored PKCE verifier.
    """
    # 1. Retrieve the saved verifier from the database
    token_record = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
    if not token_record or not token_record.pkce_verifier:
        raise ValueError("PKCE verifier not found. Please restart the authorization flow.")

    verifier = token_record.pkce_verifier

    # 2. Setup the flow
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    # 3. Swap the code, passing the verifier!
    flow.fetch_token(code=code, code_verifier=verifier)
    creds = flow.credentials

    # 4. Update the database with real tokens and clear the verifier
    token_record.access_token = creds.token
    token_record.refresh_token = creds.refresh_token or token_record.refresh_token
    token_record.expires_at = creds.expiry
    token_record.scopes = json.dumps(SCOPES)
    token_record.pkce_verifier = None # Clean up!

    db.commit()
    db.refresh(token_record)
    return token_record

def get_gmail_service(db: Session, user_id: str):
    """
    Retrieves the user's tokens from the database and builds the Gmail API client.
    This is what your Agent will use to actually send emails!
    """
    token_record = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
    
    if not token_record or not token_record.refresh_token:
        raise ValueError("User has not granted Gmail API permissions yet.")

    # Reconstruct the Google Credentials object from our database
    creds = Credentials(
        token=token_record.access_token,
        refresh_token=token_record.refresh_token,
        token_uri=CLIENT_CONFIG["web"]["token_uri"],
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=json.loads(token_record.scopes) if token_record.scopes else SCOPES
    )

    # Build and return the actual Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service


def list_gmail_labels(service) -> list:
    """Returns a list of all labels (folders) in the user's Gmail."""
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    return [{"id": label['id'], "name": label['name']} for label in labels]

def create_gmail_label(service, label_name: str) -> dict:
    """Creates a new custom label (folder) in Gmail."""
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    created_label = service.users().labels().create(userId='me', body=label_object).execute()
    return {"id": created_label['id'], "name": created_label['name']}

def modify_email_labels(service, gmail_id: str, add_labels: list = None, remove_labels: list = None) -> dict:
    """
    Applies or removes labels from a specific email. 
    (e.g., passing remove_labels=['UNREAD'] marks it as read).
    """
    body = {}
    if add_labels:
        body['addLabelIds'] = add_labels
    if remove_labels:
        body['removeLabelIds'] = remove_labels

    modified_msg = service.users().messages().modify(userId='me', id=gmail_id, body=body).execute()
    return {"gmail_id": modified_msg['id'], "current_labels": modified_msg['labelIds']}