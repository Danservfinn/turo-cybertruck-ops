"""
Tessie Sync Script
Syncs trips and charging sessions from Tessie API to Supabase
"""

import os
import requests
from datetime import datetime, timezone
from supabase import create_client, Client

# Configuration
TESSIE_TOKEN = os.environ.get("TESSIE_API_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
VIN = os.environ.get("CYBERTRUCK_VIN")

TESSIE_BASE = "https://api.tessie.com"

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_vehicle_id(supabase: Client) -> str:
    """Get the vehicle UUID from the database"""
    result = supabase.table("vehicles").select("id").eq("vin", VIN).execute()
    if result.data:
        return result.data[0]["id"]
    raise ValueError(f"Vehicle with VIN {VIN} not found in database")

def tessie_get(endpoint: str) -> dict:
    """Make a GET request to Tessie API"""
    url = f"{TESSIE_BASE}/{VIN}/{endpoint}"
    headers = {"Authorization": f"Bearer {TESSIE_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def unix_to_iso(timestamp) -> str | None:
    """Convert Unix timestamp to ISO format string"""
    if timestamp is None:
        return None
    try:
        # Handle both int and string timestamps
        ts = int(timestamp) if isinstance(timestamp, str) else timestamp
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return None

def sync_drives(supabase: Client, vehicle_id: str):
    """Sync drive/trip data from Tessie"""
    print("Syncing drives from Tessie...")
    
    # Get drives from Tessie
    try:
        drives_data = tessie_get("drives")
        drives = drives_data.get("results", [])
        print(f"  Found {len(drives)} drives from Tessie")
    except Exception as e:
        print(f"Error fetching drives: {e}")
        return
    
    # Get existing Tessie IDs to avoid duplicates
    existing = supabase.table("trips").select("tessie_id").execute()
    existing_ids = {row["tessie_id"] for row in existing.data if row.get("tessie_id")}
    
    new_count = 0
    error_count = 0
    
    for drive in drives:
        drive_id = str(drive.get("id", ""))
        
        if not drive_id or drive_id in existing_ids:
            continue
        
        # Convert Unix timestamps to ISO format
        started_at = unix_to_iso(drive.get("started_at"))
        ended_at = unix_to_iso(drive.get("ended_at"))
        
        if not started_at:
            print(f"  Skipping trip {drive_id}: invalid start time")
            continue
        
        record = {
            "vehicle_id": vehicle_id,
            "tessie_id": drive_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "start_odometer": drive.get("starting_odometer"),
            "end_odometer": drive.get("ending_odometer"),
            "purpose": "untagged",  # User will tag business vs personal
        }
        
        try:
            supabase.table("trips").insert(record).execute()
            new_count += 1
            print(f"  Added trip: {drive_id} ({started_at[:10]})")
        except Exception as e:
            error_count += 1
            print(f"  Error inserting trip {drive_id}: {e}")
    
    print(f"Synced {new_count} new trips ({error_count} errors)")

def sync_charges(supabase: Client, vehicle_id: str):
    """Sync charging sessions from Tessie"""
    print("Syncing charging sessions from Tessie...")
    
    # Get charges from Tessie
    try:
        charges_data = tessie_get("charges")
        charges = charges_data.get("results", [])
        print(f"  Found {len(charges)} charging sessions from Tessie")
    except Exception as e:
        print(f"Error fetching charges: {e}")
        return
    
    # Get existing Tessie IDs
    existing = supabase.table("charging_sessions").select("tessie_id").execute()
    existing_ids = {row["tessie_id"] for row in existing.data if row.get("tessie_id")}
    
    new_count = 0
    error_count = 0
    
    for charge in charges:
        charge_id = str(charge.get("id", ""))
        
        if not charge_id or charge_id in existing_ids:
            continue
        
        # Convert timestamps
        started_at = unix_to_iso(charge.get("started_at"))
        ended_at = unix_to_iso(charge.get("ended_at"))
        
        if not started_at:
            print(f"  Skipping charge {charge_id}: invalid start time")
            continue
        
        is_supercharger = charge.get("is_supercharger", False)
        location = charge.get("location", {})
        location_name = location.get("name", "") if isinstance(location, dict) else str(location)
        
        # Detect home charging (customize this based on your home location)
        is_home = "home" in location_name.lower() if location_name else False
        
        record = {
            "vehicle_id": vehicle_id,
            "tessie_id": charge_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "kwh_added": charge.get("energy_added"),
            "cost": charge.get("cost") if is_supercharger else None,
            "location": location_name,
            "is_supercharger": is_supercharger,
            "is_home": is_home,
        }
        
        try:
            supabase.table("charging_sessions").insert(record).execute()
            new_count += 1
            print(f"  Added charge: {charge_id} ({location_name or 'Unknown location'})")
        except Exception as e:
            error_count += 1
            print(f"  Error inserting charge {charge_id}: {e}")
    
    print(f"Synced {new_count} new charging sessions ({error_count} errors)")

def sync_odometer(supabase: Client, vehicle_id: str):
    """Record current odometer reading"""
    print("Recording odometer reading...")
    
    try:
        state = tessie_get("state")
        odometer = state.get("vehicle_state", {}).get("odometer")
        
        if odometer:
            record = {
                "vehicle_id": vehicle_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "odometer_miles": odometer,
                "source": "tessie",
            }
            supabase.table("odometer_logs").insert(record).execute()
            print(f"  Recorded odometer: {odometer:.1f} miles")
    except Exception as e:
        print(f"Error recording odometer: {e}")

def update_sync_state(supabase: Client, sync_type: str):
    """Update the last sync timestamp"""
    supabase.table("sync_state").upsert({
        "id": sync_type,
        "last_sync_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

def main():
    print(f"Starting Tessie sync at {datetime.now(timezone.utc).isoformat()}")
    print(f"VIN: {VIN}")
    
    supabase = get_supabase()
    vehicle_id = get_vehicle_id(supabase)
    print(f"Vehicle ID: {vehicle_id}")
    
    sync_drives(supabase, vehicle_id)
    sync_charges(supabase, vehicle_id)
    sync_odometer(supabase, vehicle_id)
    
    update_sync_state(supabase, "tessie")
    print("\nTessie sync complete!")

if __name__ == "__main__":
    main()
