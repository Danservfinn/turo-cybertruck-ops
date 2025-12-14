"""
Gmail Checker for Turo Messages
Checks Gmail for new Turo notification emails and extracts message content.
"""

import os
import json
import base64
import re
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.modify']

# State file to track processed messages
STATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'state', 'processed_emails.json')

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'gmail_token.pickle')
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'gmail_credentials.json')
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Gmail credentials not found at {creds_path}. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def load_processed_emails():
    """Load set of already-processed email IDs."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_emails(processed: set):
    """Save processed email IDs."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(list(processed), f)

def parse_turo_email(message_data: dict) -> dict | None:
    """
    Parse a Turo notification email and extract message details.
    Returns dict with guest_name, message_content, trip_dates, etc.
    """
    headers = {h['name']: h['value'] for h in message_data['payload']['headers']}
    subject = headers.get('Subject', '')
    
    # Check if this is a Turo message notification
    if 'turo' not in headers.get('From', '').lower():
        return None
    if 'message' not in subject.lower() and 'sent you' not in subject.lower():
        return None
    
    # Get email body
    body = ''
    payload = message_data['payload']
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
            elif part['mimeType'] == 'text/html' and not body:
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    
    # Extract guest name from subject (e.g., "John D. sent you a message")
    guest_match = re.search(r'(\w+\s*\w*\.?)\s+sent you', subject, re.IGNORECASE)
    guest_name = guest_match.group(1) if guest_match else "Guest"
    
    # Extract trip dates if present
    date_match = re.search(r'(\w+\s+\d+)\s*[-–]\s*(\w+\s+\d+)', body)
    trip_dates = f"{date_match.group(1)} - {date_match.group(2)}" if date_match else None
    
    # Extract the actual message content
    # Turo emails typically have the message in quotes or a specific section
    message_patterns = [
        r'"([^"]+)"',  # Quoted message
        r'Message:\s*(.+?)(?:\n\n|\Z)',  # "Message:" label
        r'wrote:\s*(.+?)(?:\n\n|\Z)',  # "wrote:" pattern
    ]
    
    message_content = None
    for pattern in message_patterns:
        match = re.search(pattern, body, re.DOTALL | re.IGNORECASE)
        if match:
            message_content = match.group(1).strip()
            break
    
    if not message_content:
        # Fallback: use a cleaned portion of the body
        message_content = body[:500].strip()
    
    return {
        'email_id': message_data['id'],
        'guest_name': guest_name,
        'message_content': message_content,
        'trip_dates': trip_dates,
        'subject': subject,
        'received_at': datetime.now(timezone.utc).isoformat(),
    }

def check_for_new_messages() -> list[dict]:
    """
    Check Gmail for new Turo messages.
    Returns list of parsed message dictionaries.
    """
    print(f"Checking Gmail at {datetime.now(timezone.utc).isoformat()}")
    
    service = get_gmail_service()
    processed = load_processed_emails()
    
    # Search for Turo messages from the last 24 hours
    query = 'from:turo.com subject:message newer_than:1d'
    
    try:
        results = service.users().messages().list(
            userId='me', 
            q=query,
            maxResults=10
        ).execute()
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []
    
    messages = results.get('messages', [])
    print(f"Found {len(messages)} potential Turo messages")
    
    new_messages = []
    
    for msg in messages:
        if msg['id'] in processed:
            continue
        
        # Fetch full message
        try:
            full_msg = service.users().messages().get(
                userId='me', 
                id=msg['id'],
                format='full'
            ).execute()
        except Exception as e:
            print(f"Error fetching message {msg['id']}: {e}")
            continue
        
        parsed = parse_turo_email(full_msg)
        
        if parsed:
            new_messages.append(parsed)
            processed.add(msg['id'])
            print(f"  New message from {parsed['guest_name']}")
    
    save_processed_emails(processed)
    print(f"Found {len(new_messages)} new messages to process")
    
    return new_messages

if __name__ == "__main__":
    messages = check_for_new_messages()
    for msg in messages:
        print(f"\n--- Message from {msg['guest_name']} ---")
        print(f"Trip: {msg.get('trip_dates', 'N/A')}")
        print(f"Content: {msg['message_content'][:200]}...")
