# Turo Cybertruck Operations System

> **Last Updated:** December 13, 2025
> **Status:** Fully Operational
> **Owner:** Daniel (d@pantheo.co)

---

## 🤖 Agent Instructions

**If you are an AI agent reading this file:** This document contains everything you need to understand, maintain, and extend this automated accounting system for a Turo Cybertruck rental business. Read this entire file before making changes.

### Quick Context
- **Business:** Single Tesla Cybertruck Cyberbeast rented on Turo in Raleigh, NC
- **Goal:** Automated accounting, tax optimization, and operations management
- **Stack:** Supabase (Postgres) + GitHub Actions + Tessie + SimpleFIN + Claude API

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Tessie     │    │  SimpleFIN   │    │    Turo      │          │
│  │  (Tesla API) │    │ (Bank: Novo) │    │  (Manual)    │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│         │ Hourly            │ Daily             │ Manual            │
│         ▼                   ▼                   ▼                   │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                   GitHub Actions                          │      │
│  │  ┌────────────────┐  ┌────────────────┐                  │      │
│  │  │ hourly-tessie  │  │  daily-sync    │                  │      │
│  │  │   .yml         │  │    .yml        │                  │      │
│  │  └────────────────┘  └────────────────┘                  │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                     SUPABASE                              │      │
│  │                    (Postgres)                             │      │
│  │                                                           │      │
│  │  Tables:           Views:                                 │      │
│  │  ├── vehicles      ├── ytd_business_use                  │      │
│  │  ├── trips         ├── monthly_revenue                   │      │
│  │  ├── bookings      ├── expenses_allocated                │      │
│  │  ├── charging_sessions  ├── tax_method_comparison        │      │
│  │  ├── expense_intake     ├── charging_costs               │      │
│  │  ├── expenses           └── pending_expenses             │      │
│  │  ├── revenue                                              │      │
│  │  ├── depreciation_schedule                                │      │
│  │  ├── odometer_logs                                        │      │
│  │  └── sync_state                                           │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                   AI AGENT ACCESS                         │      │
│  │         (Query via Supabase API or SQL Editor)           │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Credentials & Configuration

### Supabase
| Key | Value |
|-----|-------|
| Project URL | `https://ycsdpcggyyitutsvplvd.supabase.co` |
| Project ID | `ycsdpcggyyitutsvplvd` |
| Region | AWS us-west-2 |
| Anon Key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljc2RwY2dneXlpdHV0c3ZwbHZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2NDcwMTIsImV4cCI6MjA4MTIyMzAxMn0.PsYAISfxP0hkuAeDe2CGGWkOUvR81zT3oGI7MHhA7gQ` |
| Service Role Key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljc2RwY2dneXlpdHV0c3ZwbHZkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTY0NzAxMiwiZXhwIjoyMDgxMjIzMDEyfQ.jaSiGK3bg_jC1hslrp-uU_1Kt5mBm-d0uYZxbpryjuQ` |

### Vehicle
| Key | Value |
|-----|-------|
| Vehicle UUID | `63bd4029-46de-441a-b2dd-7bde67800d4e` |
| VIN | `7G2CEHEE6RA032607` |
| Model | 2024 Tesla Cybertruck Cyberbeast |
| Purchase Price | $86,514.85 |
| Date in Service | December 15, 2025 |
| GVWR | 6,843 lbs (Heavy vehicle - Section 179 eligible) |
| Home Charging Rate | $0.341/kWh |

### API Tokens
| Service | Token Location |
|---------|----------------|
| Tessie | `.env` file and GitHub Secrets |
| SimpleFIN | `.env` file and GitHub Secrets |
| Anthropic | `.env` file and GitHub Secrets |

> ⚠️ **Security Note:** Actual tokens are stored in `.env` (local) and GitHub Secrets (automation). Never commit `.env` to git.

---

## 📁 Project Structure

```
/Users/kurultai/turo-cybertruck-ops/
├── .github/
│   └── workflows/
│       ├── hourly-tessie.yml      # Runs every hour - syncs Tesla data
│       └── daily-sync.yml         # Runs 6 AM UTC - bank sync + AI categorization
├── scripts/
│   ├── sync_tessie.py             # Pulls trips, charging, odometer from Tessie
│   ├── sync_simplefin.py          # Pulls transactions from Novo bank
│   └── categorize_expenses.py     # AI categorization using Claude
├── .env                           # Local environment variables (not in git)
├── .gitignore
├── requirements.txt
├── setup.sh                       # Initial setup script
├── README.md                      # Basic readme
└── SYSTEM.md                      # THIS FILE - comprehensive system docs
```

---

## 🗄️ Database Schema

### Core Tables

#### `vehicles`
Primary vehicle record with tax-relevant info.
```sql
id UUID PRIMARY KEY
name TEXT                          -- "Cybertruck Cyberbeast - Raleigh"
vin TEXT UNIQUE                    -- "7G2CEHEE6RA032607"
purchase_price DECIMAL(12,2)       -- 86514.85
purchase_date DATE
date_in_service DATE               -- When Turo rentals started
gvwr_lbs INTEGER                   -- 6843 (for Section 179 eligibility)
is_heavy_vehicle BOOLEAN           -- Auto-calculated: gvwr > 6000
home_charging_rate_kwh DECIMAL     -- 0.341
```

#### `trips`
All drives from Tessie. User tags as business/personal.
```sql
id UUID PRIMARY KEY
vehicle_id UUID REFERENCES vehicles
tessie_id TEXT UNIQUE              -- Tessie's trip ID
started_at TIMESTAMPTZ
ended_at TIMESTAMPTZ
start_odometer DECIMAL
end_odometer DECIMAL
miles DECIMAL                      -- Auto-calculated
purpose TEXT                       -- 'business', 'personal', 'untagged'
booking_id UUID                    -- Links to Turo booking if applicable
```

#### `bookings`
Turo reservations (manually entered for now).
```sql
id UUID PRIMARY KEY
vehicle_id UUID REFERENCES vehicles
turo_trip_id TEXT
guest_name TEXT
start_date DATE
end_date DATE
days INTEGER                       -- Auto-calculated
gross_revenue DECIMAL
turo_fees DECIMAL
net_revenue DECIMAL
miles_included INTEGER
actual_miles DECIMAL
overage_fees DECIMAL
rating INTEGER                     -- 1-5
```

#### `charging_sessions`
Charging data from Tessie.
```sql
id UUID PRIMARY KEY
vehicle_id UUID REFERENCES vehicles
tessie_id TEXT UNIQUE
started_at TIMESTAMPTZ
ended_at TIMESTAMPTZ
kwh_added DECIMAL
cost DECIMAL                       -- Actual cost (Supercharger)
calculated_cost DECIMAL            -- Computed for home charging
location TEXT
is_supercharger BOOLEAN
is_home BOOLEAN
```

#### `expense_intake`
Raw transactions from SimpleFIN before categorization.
```sql
id UUID PRIMARY KEY
source TEXT                        -- 'simplefin', 'manual'
simplefin_id TEXT UNIQUE
raw_description TEXT
amount DECIMAL
is_income BOOLEAN
transaction_date DATE
account_name TEXT
status TEXT                        -- 'pending', 'processed', 'flagged'
ai_category TEXT
ai_confidence DECIMAL
ai_notes TEXT
```

#### `expenses`
Categorized expenses ready for tax reporting.
```sql
id UUID PRIMARY KEY
intake_id UUID REFERENCES expense_intake
vehicle_id UUID REFERENCES vehicles
transaction_date DATE
category TEXT                      -- IRS-aligned categories (see below)
description TEXT
amount DECIMAL
is_deductible BOOLEAN
allocation_method TEXT             -- 'business_use_pct', 'full', 'none', 'fixed_pct'
fixed_allocation_pct DECIMAL
```

#### `revenue`
Income records from Turo payouts.
```sql
id UUID PRIMARY KEY
intake_id UUID REFERENCES expense_intake
vehicle_id UUID REFERENCES vehicles
booking_id UUID REFERENCES bookings
transaction_date DATE
amount DECIMAL
source TEXT                        -- 'turo', 'other'
```

#### `depreciation_schedule`
Yearly depreciation tracking for tax purposes.
```sql
id UUID PRIMARY KEY
vehicle_id UUID REFERENCES vehicles
tax_year INTEGER
method TEXT                        -- 'section_179', 'bonus_100', 'macrs_5yr'
basis DECIMAL
business_use_pct DECIMAL
depreciation_amount DECIMAL
cumulative_depreciation DECIMAL
```

### Expense Categories (IRS Schedule C Aligned)
```
vehicle_insurance
vehicle_maintenance
vehicle_cleaning
vehicle_registration
charging_supercharger
charging_home
charging_other
turo_fees
parking_tolls
professional_services
software_subscriptions
other_deductible
non_deductible
```

### Key Views

#### `ytd_business_use`
Calculates business use percentage by year.
```sql
SELECT * FROM ytd_business_use WHERE tax_year = 2025;
-- Returns: vehicle_id, tax_year, total_miles, business_miles, business_use_pct
```

#### `tax_method_comparison`
Compares standard mileage vs actual expense methods.
```sql
SELECT * FROM tax_method_comparison WHERE tax_year = 2025;
-- Returns: standard_mileage_deduction, actual_expense_deduction, recommended_method
```

#### `pending_expenses`
Shows expenses awaiting categorization/review.
```sql
SELECT * FROM pending_expenses;
```

---

## ⚙️ Automation Workflows

### Hourly: Tessie Sync
**File:** `.github/workflows/hourly-tessie.yml`
**Schedule:** Every hour at minute 0
**What it does:**
1. Pulls new trips from Tessie API
2. Pulls new charging sessions
3. Records current odometer reading
4. Writes to Supabase

### Daily: Bank Sync + AI Categorization
**File:** `.github/workflows/daily-sync.yml`
**Schedule:** 6 AM UTC (1 AM EST)
**What it does:**
1. Pulls transactions from Novo via SimpleFIN
2. Runs AI categorization on pending expenses
3. Auto-processes high-confidence categorizations (≥70%)
4. Flags low-confidence for manual review

---

## 🧠 AI Categorization Logic

Located in `scripts/categorize_expenses.py`

### Process:
1. Fetch all `expense_intake` records with status = 'pending'
2. For each expense:
   - Try keyword matching first (fast, free)
   - Fall back to Claude API if no keyword match
3. If confidence ≥ 70%: auto-create `expenses` record, mark as 'processed'
4. If confidence < 70%: mark as 'flagged' for manual review

### Keyword Rules (checked first):
```python
KEYWORD_RULES = {
    "vehicle_insurance": ["insurance", "geico", "progressive"],
    "vehicle_maintenance": ["repair", "service", "tire", "brake"],
    "vehicle_cleaning": ["car wash", "detail", "cleaning"],
    "charging_supercharger": ["tesla", "supercharger"],
    "turo_fees": ["turo"],
    "parking_tolls": ["parking", "toll", "ez pass"],
    "software_subscriptions": ["tessie", "subscription", "software"],
    "professional_services": ["accountant", "cpa", "legal"],
}
```

### Claude API Prompt:
The AI receives transaction details and must categorize into one of the defined categories with a confidence score.

---

## 💰 Tax Optimization Features

### Section 179 Eligibility
The Cybertruck qualifies as a "heavy vehicle" (GVWR > 6,000 lbs):
- Can deduct up to 100% of purchase price in year one
- Limited to business use percentage
- Alternative: MACRS 5-year depreciation

### Business Use Percentage
```
Business Use % = Business Miles / Total Miles
```
- Trips must be tagged as 'business' or 'personal'
- Affects allocation of mixed expenses (insurance, etc.)

### Tax Method Comparison
The system calculates both methods automatically:

**Standard Mileage (2025):** Business Miles × $0.70/mile

**Actual Expense:** 
- Depreciation (allocated by business use %)
- Charging costs
- Insurance (allocated)
- Maintenance
- Cleaning
- Platform fees (100% business)
- Software subscriptions

Query `tax_method_comparison` view to see which is better.

---

## 📋 Manual Tasks

### Weekly (~10 minutes)
1. **Tag trips as business/personal**
   - Go to Supabase Table Editor → `trips`
   - Filter: `purpose = 'untagged'`
   - Update each trip's `purpose` field

2. **Review flagged expenses**
   - Query: `SELECT * FROM pending_expenses`
   - Update category if needed, change status to 'processed'

3. **Add Turo bookings** (until automated)
   - Go to Table Editor → `bookings`
   - Add new reservations manually

### Monthly
- Review revenue totals
- Check depreciation schedule
- Verify business use % is tracking correctly

### Tax Time (Yearly)
```sql
-- Get Schedule C summary
SELECT * FROM tax_method_comparison WHERE tax_year = 2025;

-- Get expenses by category
SELECT category, SUM(deductible_amount) 
FROM expenses_allocated 
WHERE tax_year = 2025 
GROUP BY category;

-- Get total revenue
SELECT SUM(amount) FROM revenue 
WHERE EXTRACT(YEAR FROM transaction_date) = 2025;
```

---

## 🔮 Future Enhancements

### Planned / Possible Additions

#### 1. Turo API Integration
- **Status:** Not started
- **Challenge:** Turo has no official API; would require browser automation
- **Approach:** Puppeteer/Playwright to scrape booking data
- **Benefit:** Auto-import bookings, eliminate manual entry

#### 2. Automatic Trip Tagging
- **Status:** Not started
- **Approach:** Use booking dates to auto-tag trips as business
- **Logic:** If trip overlaps with a booking date range → business

#### 3. Receipt Scanning
- **Status:** Not started
- **Approach:** Add receipt_url field, use Claude vision to extract data
- **Benefit:** Better documentation for audits

#### 4. Multi-Vehicle Support
- **Status:** Schema ready (vehicle_id on all tables)
- **Approach:** Add more vehicles to `vehicles` table
- **Changes needed:** Update sync scripts to loop through vehicles

#### 5. Real-time Alerts
- **Status:** Not started
- **Approach:** Add Slack/SMS notifications
- **Triggers:** New booking, expense flagged, low utilization

#### 6. Pricing Optimization Agent
- **Status:** Not started
- **Approach:** Pull local events (NC State games, concerts), adjust Turo pricing
- **Data needed:** Event calendars, historical booking patterns

#### 7. Dashboard / UI
- **Status:** Not started
- **Options:** 
  - Supabase built-in dashboard
  - Custom React app
  - Retool/Appsmith

---

## 🛠️ Development Guide

### Local Development Setup
```bash
cd /Users/kurultai/turo-cybertruck-ops
source .env
pip install -r requirements.txt

# Test individual scripts
python scripts/sync_tessie.py
python scripts/sync_simplefin.py
python scripts/categorize_expenses.py
```

### Adding a New Sync Script
1. Create `scripts/sync_newservice.py`
2. Follow pattern of existing scripts:
   - Load env vars
   - Connect to Supabase
   - Fetch from external API
   - Upsert to database
   - Update `sync_state`
3. Add to appropriate GitHub workflow

### Adding a New Expense Category
1. Update `expenses` table CHECK constraint (requires migration)
2. Update `CATEGORIES` list in `categorize_expenses.py`
3. Add keyword rules if applicable

### Database Migrations
Run SQL in Supabase SQL Editor:
```sql
-- Example: Add new column
ALTER TABLE trips ADD COLUMN weather TEXT;
```

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Supabase Dashboard | https://supabase.com/dashboard/project/ycsdpcggyyitutsvplvd |
| Supabase Table Editor | https://supabase.com/dashboard/project/ycsdpcggyyitutsvplvd/editor |
| Supabase SQL Editor | https://supabase.com/dashboard/project/ycsdpcggyyitutsvplvd/sql/new |
| GitHub Repo | https://github.com/Danservfinn/turo-cybertruck-ops |
| GitHub Actions | (repo) → Actions tab |
| Anthropic Console | https://console.anthropic.com |
| SimpleFIN | https://beta-bridge.simplefin.org |
| Tessie | https://tessie.com |

---

## 📞 Support & Troubleshooting

### Common Issues

**"supabase_url is required" error**
- `.env` file not sourced or missing `export` keyword
- Fix: `source .env` before running scripts

**Tessie returns empty data**
- Vehicle may be asleep
- Check VIN is correct
- Verify Tessie subscription is active

**SimpleFIN "Forbidden" error**
- Access URL expired or already claimed
- Generate new token at SimpleFIN dashboard

**AI categorization fails**
- Check Anthropic API credits
- Verify ANTHROPIC_API_KEY is set

### Logs
- GitHub Actions: Check workflow run logs in repo → Actions
- Local: Scripts print to stdout

---

## 📝 Changelog

### December 13, 2025 - Initial Setup
- Created Supabase database with full schema
- Set up Tessie integration (hourly sync)
- Set up SimpleFIN integration (daily sync)
- Implemented AI expense categorization
- Configured GitHub Actions automation
- Created comprehensive documentation

---

## 🤖 Agent Handoff Notes

**For future AI agents continuing this project:**

1. **Read this entire file first** - it contains all context needed
2. **Check `.env` for current credentials** - they may have been rotated
3. **Query `sync_state` table** - shows last successful sync times
4. **Query `pending_expenses`** - shows items needing attention
5. **The user (Daniel) prefers:**
   - Direct API integrations over third-party tools (no Zapier)
   - Simple solutions that scale up as needed
   - Clear explanations of technical tradeoffs
6. **Current limitations:**
   - Turo bookings are manual (no API)
   - Trip tagging is manual
   - No UI/dashboard yet

**To pick up where we left off:**
```sql
-- Check system health
SELECT * FROM sync_state;
SELECT COUNT(*) as pending FROM expense_intake WHERE status = 'pending';
SELECT COUNT(*) as flagged FROM expense_intake WHERE status = 'flagged';
SELECT * FROM ytd_business_use;
```

---

*This document is the source of truth for the Turo Cybertruck Operations system. Keep it updated as changes are made.*
