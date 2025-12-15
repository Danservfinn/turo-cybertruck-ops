# CLAUDE.md - Turo Cybertruck Operations

> **Read this first.** This file gives AI assistants everything needed to understand, maintain, and extend this system.

## Project Overview

Automated operations system for a single Tesla Cybertruck Cyberbeast ("Aether") rented on Turo in Raleigh, NC. Handles accounting, tax optimization, and guest communications.

**Owner:** Daniel (d@pantheo.co)

## Quick Commands
```bash
# Setup
cd /Users/kurultai/turo-cybertruck-ops
source .env

# Test individual components
python scripts/sync_tessie.py              # Sync Tesla data
python scripts/sync_simplefin.py           # Sync bank transactions
python scripts/categorize_expenses.py      # AI categorize expenses
python messaging/scripts/workflow.py       # Check for guest messages
python messaging/scripts/parse_bookings.py # Parse booking emails
python scripts/auto_tag_trips.py           # Auto-tag trips as business/personal
python scripts/auto_tag_trips.py summary   # View trip tagging summary

# Deploy changes
git add . && git commit -m "description" && git push
```

## Architecture
```
DATA SOURCES
- Tessie (Tesla API)     → Trips, charging, odometer (hourly)
- SimpleFIN (Novo Bank)  → Transactions (daily)
- Gmail                  → Turo messages & bookings (5 min)

GITHUB ACTIONS
- hourly-tessie.yml      → Sync Tesla data
- check-messages.yml     → AI response drafts → ntfy push
- daily-sync.yml         → Bank sync, categorize, tag trips

SUPABASE
- Tables: vehicles, trips, bookings, charging_sessions, expense_intake, expenses, revenue, depreciation
- Views: ytd_business_use, tax_method_comparison
```

## Credentials

Stored in `.env` (local) and GitHub Secrets (automation):

- SUPABASE_URL: https://ycsdpcggyyitutsvplvd.supabase.co
- SUPABASE_SERVICE_KEY: Database auth
- TESSIE_API_TOKEN: Tesla data API
- SIMPLEFIN_ACCESS_URL: Bank connection
- ANTHROPIC_API_KEY: Claude AI
- GMAIL_CREDENTIALS: Gmail OAuth (base64)
- GMAIL_TOKEN: Gmail token (base64)
- NTFY_TOPIC: turo-aether-messages
- VEHICLE_ID: 63bd4029-46de-441a-b2dd-7bde67800d4e
- CYBERTRUCK_VIN: 7G2CEHEE6RA032607

## Vehicle Details

- Name: Aether
- Model: 2024 Tesla Cybertruck Cyberbeast
- Purchase: $86,514.85
- GVWR: 6,843 lbs (Section 179 eligible)
- Features: Full Self-Driving (FSD) included
- Home charging rate: $0.341/kWh

## Business Rules

Rental Policies:
- Delivery: Up to 15 miles, $115 (includes RDU)
- Mileage: 200 mi/day included
- Return charge: 70% minimum (or $30 fee)
- Cleaning: Zips Car Wash membership included
- Equipment fees: Adapter $50, keycard $100

Pricing (current):
- Base: ~$150/day
- 3-day: 10% off, 1-week: 10% off, 2-week: 15% off, 3-week: 20% off, Monthly: 25% off

## Key Files

- SYSTEM.md: Comprehensive system documentation
- messaging/SETUP.md: Guest messaging setup guide
- messaging/config/*.md: AI context (vehicle, policies, FAQ, tone)
- scripts/sync_tessie.py: Tesla data sync
- scripts/sync_simplefin.py: Bank transaction sync
- scripts/categorize_expenses.py: AI expense categorization
- scripts/auto_tag_trips.py: Auto-tag trips by booking dates
- messaging/scripts/workflow.py: Guest message workflow
- messaging/scripts/parse_bookings.py: Booking email parser

## Troubleshooting

- .env not loading: Run source .env
- Gmail auth failed: Refresh token
- No Tessie data: Check VIN, Tessie subscription
- SimpleFIN forbidden: Generate new access URL
- AI categorization fails: Check Anthropic credits
- ntfy not working: Verify topic subscription in app

## Links

- Supabase: https://supabase.com/dashboard/project/ycsdpcggyyitutsvplvd
- GitHub: https://github.com/Danservfinn/turo-cybertruck-ops
- ntfy: https://ntfy.sh/turo-aether-messages
