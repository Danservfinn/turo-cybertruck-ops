"""
SimpleFIN Sync Script
Syncs bank transactions from SimpleFIN to Supabase expense_intake table
"""

import os
import requests
from datetime import datetime, timedelta
from supabase import create_client, Client

# Configuration
SIMPLEFIN_ACCESS_URL = os.environ.get("SIMPLEFIN_ACCESS_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_simplefin_transactions(days_back: int = 30) -> dict:
    """Fetch transactions from SimpleFIN"""
    if not SIMPLEFIN_ACCESS_URL:
        raise ValueError("SIMPLEFIN_ACCESS_URL not set")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Build request URL with date params
    params = {
        "start-date": int(start_date.timestamp()),
        "end-date": int(end_date.timestamp()),
    }
    
    # SimpleFIN access URL includes credentials
    url = f"{SIMPLEFIN_ACCESS_URL}/accounts"
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def sync_transactions(supabase: Client):
    """Sync transactions from SimpleFIN to expense_intake"""
    print("Fetching transactions from SimpleFIN...")
    
    try:
        data = fetch_simplefin_transactions(days_back=60)
    except Exception as e:
        print(f"Error fetching from SimpleFIN: {e}")
        return
    
    # Get existing SimpleFIN IDs to avoid duplicates
    existing = supabase.table("expense_intake").select("simplefin_id").execute()
    existing_ids = {row["simplefin_id"] for row in existing.data if row.get("simplefin_id")}
    
    new_count = 0
    accounts = data.get("accounts", [])
    
    for account in accounts:
        account_name = account.get("name", "Unknown Account")
        org_name = account.get("org", {}).get("name", "")
        
        print(f"Processing account: {account_name} ({org_name})")
        
        transactions = account.get("transactions", [])
        
        for txn in transactions:
            txn_id = txn.get("id", "")
            
            if not txn_id or txn_id in existing_ids:
                continue
            
            # Parse amount (SimpleFIN: negative = outflow, positive = inflow)
            amount = float(txn.get("amount", 0))
            is_income = amount > 0
            
            # Parse date
            posted_timestamp = txn.get("posted")
            if posted_timestamp:
                txn_date = datetime.fromtimestamp(posted_timestamp).date().isoformat()
            else:
                txn_date = datetime.now().date().isoformat()
            
            record = {
                "source": "simplefin",
                "simplefin_id": txn_id,
                "raw_description": txn.get("description", ""),
                "amount": abs(amount),
                "is_income": is_income,
                "transaction_date": txn_date,
                "account_name": f"{org_name} - {account_name}",
                "status": "pending",
            }
            
            try:
                supabase.table("expense_intake").insert(record).execute()
                new_count += 1
                print(f"  Added: {txn.get('description', '')[:50]} ${abs(amount):.2f}")
            except Exception as e:
                print(f"  Error inserting transaction {txn_id}: {e}")
    
    print(f"Synced {new_count} new transactions")

def update_sync_state(supabase: Client):
    """Update the last sync timestamp"""
    supabase.table("sync_state").upsert({
        "id": "simplefin",
        "last_sync_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }).execute()

def main():
    print(f"Starting SimpleFIN sync at {datetime.utcnow().isoformat()}")
    
    supabase = get_supabase()
    sync_transactions(supabase)
    update_sync_state(supabase)
    
    print("SimpleFIN sync complete!")

if __name__ == "__main__":
    main()
