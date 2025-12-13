"""
AI Expense Categorization Script
Uses Claude API to automatically categorize expenses from expense_intake
"""

import os
import json
from datetime import datetime
from anthropic import Anthropic
from supabase import create_client, Client

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
VEHICLE_ID = os.environ.get("VEHICLE_ID")

# IRS-aligned expense categories
CATEGORIES = [
    "vehicle_insurance",
    "vehicle_maintenance",
    "vehicle_cleaning",
    "vehicle_registration",
    "charging_supercharger",
    "charging_home",
    "charging_other",
    "turo_fees",
    "parking_tolls",
    "professional_services",
    "software_subscriptions",
    "other_deductible",
    "non_deductible",
]

# Keywords for auto-categorization (before AI)
KEYWORD_RULES = {
    "vehicle_insurance": ["insurance", "geico", "progressive", "state farm", "allstate"],
    "vehicle_maintenance": ["repair", "service", "maintenance", "tire", "brake", "alignment"],
    "vehicle_cleaning": ["car wash", "detail", "cleaning", "wash"],
    "charging_supercharger": ["tesla", "supercharger", "supercharge"],
    "turo_fees": ["turo"],
    "parking_tolls": ["parking", "toll", "ez pass", "sunpass"],
    "software_subscriptions": ["tessie", "subscription", "software"],
    "professional_services": ["accountant", "cpa", "legal", "attorney", "lawyer"],
}

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_anthropic() -> Anthropic:
    return Anthropic(api_key=ANTHROPIC_API_KEY)

def keyword_categorize(description: str) -> tuple[str, float]:
    """Try to categorize based on keywords first"""
    desc_lower = description.lower()
    
    for category, keywords in KEYWORD_RULES.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category, 0.9
    
    return None, 0.0

def ai_categorize(client: Anthropic, expense: dict) -> dict:
    """Use Claude to categorize an expense"""
    
    prompt = f"""Categorize this transaction for a Turo Cybertruck rental business.

Transaction:
- Date: {expense['transaction_date']}
- Amount: ${expense['amount']:.2f}
- Description: {expense['raw_description']}
- Is Income: {expense['is_income']}
- Account: {expense.get('account_name', 'Unknown')}

Valid categories (choose exactly one):
- vehicle_insurance: Car insurance payments
- vehicle_maintenance: Repairs, service, tires, parts
- vehicle_cleaning: Car wash, detailing
- vehicle_registration: DMV fees, registration
- charging_supercharger: Tesla Supercharger costs
- charging_home: Home electricity for charging (rare to see directly)
- charging_other: Other charging networks
- turo_fees: Turo platform fees
- parking_tolls: Parking fees, toll charges
- professional_services: Accountant, legal fees
- software_subscriptions: Tessie, apps, software
- other_deductible: Other business expenses
- non_deductible: Personal or non-business expenses

For Turo payouts (income), still categorize as "turo_fees" if it's a fee, or respond with is_deductible: false if it's a payout.

Respond ONLY with valid JSON (no markdown):
{{"category": "category_name", "is_deductible": true, "confidence": 0.85, "notes": "brief reason"}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text.strip()
        
        # Clean up potential markdown formatting
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        return json.loads(result_text)
    
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return {"category": "other_deductible", "is_deductible": True, "confidence": 0.3, "notes": "AI response parse error"}
    except Exception as e:
        print(f"  AI error: {e}")
        return {"category": "other_deductible", "is_deductible": True, "confidence": 0.3, "notes": f"AI error: {str(e)}"}

def process_pending_expenses(supabase: Client, anthropic_client: Anthropic):
    """Process all pending expenses"""
    print("Fetching pending expenses...")
    
    pending = supabase.table("expense_intake").select("*").eq("status", "pending").execute()
    
    if not pending.data:
        print("No pending expenses to process")
        return
    
    print(f"Processing {len(pending.data)} pending expenses...")
    
    processed = 0
    flagged = 0
    
    for expense in pending.data:
        desc = expense.get("raw_description", "")
        print(f"\nProcessing: {desc[:50]}...")
        
        # Try keyword matching first
        category, confidence = keyword_categorize(desc)
        
        if category and confidence >= 0.8:
            result = {
                "category": category,
                "is_deductible": True,
                "confidence": confidence,
                "notes": "Matched by keyword"
            }
        else:
            # Fall back to AI
            result = ai_categorize(anthropic_client, expense)
        
        category = result.get("category", "other_deductible")
        confidence = result.get("confidence", 0.5)
        is_deductible = result.get("is_deductible", True)
        notes = result.get("notes", "")
        
        # Update intake record with AI results
        supabase.table("expense_intake").update({
            "ai_category": category,
            "ai_confidence": confidence,
            "ai_notes": notes,
        }).eq("id", expense["id"]).execute()
        
        if confidence >= 0.7:
            # Auto-process high confidence
            if not expense.get("is_income", False):
                # It's an expense, create expense record
                expense_record = {
                    "intake_id": expense["id"],
                    "vehicle_id": VEHICLE_ID,
                    "transaction_date": expense["transaction_date"],
                    "category": category,
                    "description": expense["raw_description"],
                    "amount": expense["amount"],
                    "is_deductible": is_deductible,
                    "allocation_method": "business_use_pct",
                    "notes": notes,
                }
                
                try:
                    supabase.table("expenses").insert(expense_record).execute()
                except Exception as e:
                    print(f"  Error creating expense: {e}")
            else:
                # It's income, create revenue record
                revenue_record = {
                    "intake_id": expense["id"],
                    "vehicle_id": VEHICLE_ID,
                    "transaction_date": expense["transaction_date"],
                    "amount": expense["amount"],
                    "source": "turo" if "turo" in expense["raw_description"].lower() else "other",
                    "description": expense["raw_description"],
                }
                
                try:
                    supabase.table("revenue").insert(revenue_record).execute()
                except Exception as e:
                    print(f"  Error creating revenue: {e}")
            
            # Mark as processed
            supabase.table("expense_intake").update({
                "status": "processed",
                "processed_at": datetime.utcnow().isoformat(),
            }).eq("id", expense["id"]).execute()
            
            processed += 1
            print(f"  ✓ Processed: {category} (confidence: {confidence:.0%})")
        else:
            # Flag for manual review
            supabase.table("expense_intake").update({
                "status": "flagged",
            }).eq("id", expense["id"]).execute()
            
            flagged += 1
            print(f"  ? Flagged for review: {category} (confidence: {confidence:.0%})")
    
    print(f"\n{'='*50}")
    print(f"Processed: {processed}")
    print(f"Flagged for review: {flagged}")

def main():
    print(f"Starting AI categorization at {datetime.utcnow().isoformat()}")
    
    supabase = get_supabase()
    anthropic_client = get_anthropic()
    
    process_pending_expenses(supabase, anthropic_client)
    
    print("AI categorization complete!")

if __name__ == "__main__":
    main()
