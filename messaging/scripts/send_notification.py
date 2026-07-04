"""
Signal Notification Sender
Sends approval requests to Signal via signal-cli-rest-api.

SETUP REQUIRED:
This script requires signal-cli-rest-api running somewhere accessible.
See: https://github.com/bbernhard/signal-cli-rest-api

Options:
1. Self-host on a VPS ($5/mo DigitalOcean/Vultr)
2. Run locally on your Mac (for testing)
3. Use alternative: ntfy.sh (free, simpler)
"""

import os
import json
import requests
from datetime import datetime, timezone

# Configuration
SIGNAL_API_URL = os.environ.get("SIGNAL_API_URL", "http://localhost:8080")
SIGNAL_PHONE = os.environ.get("SIGNAL_PHONE", "")  # Set via env var, do not hardcode
SIGNAL_SENDER = os.environ.get("SIGNAL_SENDER")  # Registered sender number

# Alternative: ntfy.sh (free push notifications)
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "turo-aether-messages")
USE_NTFY = os.environ.get("USE_NTFY", "true").lower() == "true"

def format_approval_message(guest_name: str, message: str, proposed_response: str, 
                            trip_dates: str = None, message_id: str = None) -> str:
    """Format the approval request message."""
    
    trip_info = f"Trip: {trip_dates}\n" if trip_dates else ""
    msg_id = f"[ID: {message_id}]\n" if message_id else ""
    
    return f"""🚗 NEW TURO MESSAGE
{msg_id}
From: {guest_name}
{trip_info}
MESSAGE:
"{message}"

─────────────────────

PROPOSED RESPONSE:
"{proposed_response}"

─────────────────────

Reply:
✅ SEND - to approve
❌ DENY - to skip  
Or type your edited response"""

def send_via_signal(message: str, recipient: str = None) -> bool:
    """
    Send message via signal-cli-rest-api.
    
    Requires signal-cli-rest-api running at SIGNAL_API_URL.
    """
    recipient = recipient or SIGNAL_PHONE
    
    if not SIGNAL_SENDER:
        print("Error: SIGNAL_SENDER environment variable not set")
        return False
    
    try:
        response = requests.post(
            f"{SIGNAL_API_URL}/v2/send",
            json={
                "message": message,
                "number": SIGNAL_SENDER,
                "recipients": [recipient]
            },
            timeout=30
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✓ Signal message sent to {recipient}")
            return True
        else:
            print(f"✗ Signal API error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to Signal API at {SIGNAL_API_URL}")
        return False
    except Exception as e:
        print(f"✗ Signal error: {e}")
        return False

def send_via_ntfy(message: str, title: str = "New Turo Message") -> bool:
    """
    Send message via ntfy.sh (free push notification service).
    
    Setup:
    1. Install ntfy app on your phone
    2. Subscribe to your topic (default: turo-aether-messages)
    3. That's it!
    """
    try:
        response = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode('utf-8'),
            headers={
                "Title": title,
                "Priority": "high",
                "Tags": "car,speech_balloon"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✓ ntfy notification sent to topic: {NTFY_TOPIC}")
            return True
        else:
            print(f"✗ ntfy error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ ntfy error: {e}")
        return False

def send_approval_request(guest_name: str, message: str, proposed_response: str,
                          trip_dates: str = None, message_id: str = None) -> bool:
    """
    Send an approval request notification.
    
    Tries Signal first, falls back to ntfy.
    """
    formatted_message = format_approval_message(
        guest_name=guest_name,
        message=message,
        proposed_response=proposed_response,
        trip_dates=trip_dates,
        message_id=message_id
    )
    
    # Try ntfy first if enabled (simpler setup)
    if USE_NTFY:
        if send_via_ntfy(formatted_message, f"Message from {guest_name}"):
            return True
    
    # Try Signal
    if SIGNAL_SENDER:
        if send_via_signal(formatted_message):
            return True
    
    # All methods failed
    print("✗ Could not send notification via any method")
    print("  Configure SIGNAL_API_URL and SIGNAL_SENDER, or enable USE_NTFY")
    return False

def main():
    """Test notification sending."""
    print("Testing notification system...")
    print(f"USE_NTFY: {USE_NTFY}")
    print(f"NTFY_TOPIC: {NTFY_TOPIC}")
    print(f"SIGNAL_API_URL: {SIGNAL_API_URL}")
    print(f"SIGNAL_PHONE: {SIGNAL_PHONE}")
    print()
    
    success = send_approval_request(
        guest_name="John D.",
        message="Hi! Does the Cybertruck come with FSD?",
        proposed_response="Hi John! Yes, FSD is included and I encourage you to try it!",
        trip_dates="Dec 20-23, 2025",
        message_id="test123"
    )
    
    if success:
        print("\n✓ Test notification sent successfully!")
    else:
        print("\n✗ Test notification failed")

if __name__ == "__main__":
    main()
