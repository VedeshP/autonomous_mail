import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
# We are using 'modify' scope so we can eventually label/delete, but for now we just read.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_desktop.json', SCOPES)
            # This opens a browser window for you to log in
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def fetch_latest_email(service):
    # 1. Ask Gmail for the ID of the 1 most recent email
    print("Fetching the latest email ID...")
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
        return

    # 2. Fetch the actual full email data using that ID
    msg_id = messages[0]['id']
    print(f"Fetching full data for Email ID: {msg_id}")
    
    # We request the 'full' format to see headers, body, and attachment info
    message_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

    # 3. Save it to a file so we can analyze the JSON structure
    output_path = "sample_email.json"
    with open(output_path, "w") as f:
        json.dump(message_data, f, indent=4)
    
    print(f"\n✅ Success! Saved the raw email payload to {output_path}")
    print("Open this file in VS Code to analyze the schema.")

if __name__ == '__main__':
    # Make sure we are running this from the backend root directory
    if not os.path.exists('credentials_desktop.json'):
        print("Error: credentials_desktop.json not found in the current directory.")
        print("Please ensure you are running this script from the 'backend' folder.")
    else:
        service = authenticate_gmail()
        fetch_latest_email(service)