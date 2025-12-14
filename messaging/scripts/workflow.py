"""
Main Messaging Workflow
Orchestrates the full flow: Check Gmail → Generate Response → Send for Approval
"""

import os
import json
from datetime import datetime, timezone

from check_gmail import check_for_new_messages
from generate_response import generate_response
from send_notification import send_approval_request

# State file for pending approvals
PENDING_FILE = os.path.join(os.path.dirname(__file__), '..', 'state', 'pending_responses.json')

def load_pending() -> dict:
    """Load pending responses awaiting approval."""
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_pending(pending: dict):
    """Save pending responses."""
    os.makedirs(os.path.dirname(PENDING_FILE), exist_ok=True)
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending, f, indent=2)

def process_new_messages():
    """
    Main workflow:
    1. Check Gmail for new Turo messages
    2. Generate AI response for each
    3. Send approval request via Signal/ntfy
    4. Store pending response for later action
    """
    print(f"\n{'='*60}")
    print(f"Turo Message Processor - {datetime.now(timezone.utc).isoformat()}")
    print('='*60)
    
    # Step 1: Check for new messages
    print("\n[1/3] Checking Gmail for new Turo messages...")
    new_messages = check_for_new_messages()
    
    if not new_messages:
        print("No new messages to process.")
        return
    
    print(f"Found {len(new_messages)} new message(s)")
    
    # Load existing pending responses
    pending = load_pending()
    
    for msg in new_messages:
        email_id = msg['email_id']
        guest_name = msg['guest_name']
        message_content = msg['message_content']
        trip_dates = msg.get('trip_dates')
        
        print(f"\n[2/3] Processing message from {guest_name}...")
        print(f"      Message: {message_content[:100]}...")
        
        # Step 2: Generate AI response
        result = generate_response(
            guest_name=guest_name,
            message=message_content,
            trip_dates=trip_dates
        )
        
        if not result['response']:
            print(f"      ✗ Failed to generate response: {result['notes']}")
            continue
        
        print(f"      ✓ Generated response (confidence: {result['confidence']:.0%})")
        
        # Step 3: Send approval request
        print(f"\n[3/3] Sending approval request...")
        
        success = send_approval_request(
            guest_name=guest_name,
            message=message_content,
            proposed_response=result['response'],
            trip_dates=trip_dates,
            message_id=email_id[:8]  # Short ID for reference
        )
        
        if success:
            # Store pending response
            pending[email_id] = {
                'guest_name': guest_name,
                'original_message': message_content,
                'proposed_response': result['response'],
                'confidence': result['confidence'],
                'trip_dates': trip_dates,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending'
            }
            print(f"      ✓ Approval request sent, awaiting response")
        else:
            print(f"      ✗ Failed to send approval request")
    
    # Save pending responses
    save_pending(pending)
    
    print(f"\n{'='*60}")
    print(f"Processing complete. {len(pending)} response(s) pending approval.")
    print('='*60)

def list_pending():
    """List all pending responses awaiting approval."""
    pending = load_pending()
    
    if not pending:
        print("No pending responses.")
        return
    
    print(f"\n{len(pending)} Pending Response(s):")
    print("-" * 40)
    
    for email_id, data in pending.items():
        print(f"\nID: {email_id[:8]}")
        print(f"Guest: {data['guest_name']}")
        print(f"Trip: {data.get('trip_dates', 'N/A')}")
        print(f"Status: {data['status']}")
        print(f"Confidence: {data['confidence']:.0%}")
        print(f"Created: {data['created_at']}")

def approve_response(email_id: str, edited_response: str = None):
    """
    Mark a response as approved.
    
    Args:
        email_id: Full or partial email ID
        edited_response: Optional edited response (if None, use proposed)
    """
    pending = load_pending()
    
    # Find matching email ID
    match = None
    for eid in pending:
        if eid.startswith(email_id) or email_id in eid:
            match = eid
            break
    
    if not match:
        print(f"No pending response found for ID: {email_id}")
        return None
    
    data = pending[match]
    final_response = edited_response or data['proposed_response']
    
    # Update status
    data['status'] = 'approved'
    data['final_response'] = final_response
    data['approved_at'] = datetime.now(timezone.utc).isoformat()
    
    save_pending(pending)
    
    print(f"✓ Response approved for {data['guest_name']}")
    print(f"\nFinal response to send:")
    print(f'"{final_response}"')
    print(f"\n→ Copy this and paste into Turo chat")
    
    return final_response

def deny_response(email_id: str):
    """Mark a response as denied (skip)."""
    pending = load_pending()
    
    # Find matching email ID
    match = None
    for eid in pending:
        if eid.startswith(email_id) or email_id in eid:
            match = eid
            break
    
    if not match:
        print(f"No pending response found for ID: {email_id}")
        return
    
    data = pending[match]
    data['status'] = 'denied'
    data['denied_at'] = datetime.now(timezone.utc).isoformat()
    
    save_pending(pending)
    print(f"✓ Response denied for {data['guest_name']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Default: process new messages
        process_new_messages()
    elif sys.argv[1] == "list":
        list_pending()
    elif sys.argv[1] == "approve" and len(sys.argv) >= 3:
        edited = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else None
        approve_response(sys.argv[2], edited)
    elif sys.argv[1] == "deny" and len(sys.argv) >= 3:
        deny_response(sys.argv[2])
    else:
        print("Usage:")
        print("  python workflow.py           - Process new messages")
        print("  python workflow.py list      - List pending responses")
        print("  python workflow.py approve <id> [edited response]")
        print("  python workflow.py deny <id>")
