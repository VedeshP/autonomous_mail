import base64
from datetime import datetime
from typing import Dict, Any, Optional

from dateutil.parser import parse as parse_datetime

from app.schemas.email import EmailCreate

def parse_gmail_payload(payload: Dict[str, Any]) -> EmailCreate:
    """
    Parses the raw JSON payload from the Gmail API into our clean Pydantic schema.
    """
    # 1. First, flatten the annoying headers list into a simple dictionary
    headers = {header['name']: header['value'] for header in payload['payload']['headers']}

    # 2. Decode the body content from Base64URL
    # We prioritize the 'text/plain' part for our AI
    raw_text_body = None
    raw_html_body = None
    
    parts = payload['payload'].get('parts', [])
    for part in parts:
        if part['mimeType'] == 'text/plain':
            data = part['body'].get('data')
            if data:
                # The data is Base64URL encoded. We must add padding if needed.
                missing_padding = len(data) % 4
                if missing_padding:
                    data += '=' * (4 - missing_padding)
                raw_text_body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        elif part['mimeType'] == 'text/html':
            data = part['body'].get('data')
            if data:
                missing_padding = len(data) % 4
                if missing_padding:
                    data += '=' * (4 - missing_padding)
                raw_html_body = base64.urlsafe_b64decode(data).decode('utf-8')

    # 3. Extract the key metadata
    gmail_id = payload.get('id')
    thread_id = payload.get('threadId')
    labels = payload.get('labelIds', [])
    snippet = payload.get('snippet', '')
    
    # Extract from our flattened header dictionary, providing defaults
    sender = headers.get('From', 'Unknown Sender')
    recipient = headers.get('To', 'Unknown Recipient')
    subject = headers.get('Subject', 'No Subject')
    
    # Parse the date using the robust dateutil library
    date_str = headers.get('Date')
    date_received = parse_datetime(date_str) if date_str else datetime.utcnow()

    # 4. Assemble the clean Pydantic object
    return EmailCreate(
        gmail_id=gmail_id,
        thread_id=thread_id,
        sender=sender,
        recipient=recipient,
        subject=subject,
        date_received=date_received,
        labels=labels,
        snippet=snippet,
        raw_text_body=raw_text_body,
        raw_html_body=raw_html_body
    )