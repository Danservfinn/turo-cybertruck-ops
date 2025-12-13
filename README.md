# Turo Cybertruck Operations

Automated accounting and operations system for a Tesla Cybertruck Turo rental business.

## Features

- **Automated Tessie Sync**: Pulls trip data, charging sessions, and odometer readings
- **SimpleFIN Bank Sync**: Imports transactions from your Novo business bank account
- **AI Expense Categorization**: Uses Claude to automatically categorize expenses
- **Tax-Optimized Tracking**: Calculates business use %, compares standard mileage vs actual expenses
- **Section 179 Ready**: Tracks depreciation for heavy vehicle tax benefits

## Architecture

```
SimpleFIN (Novo) ──┐
                   │     GitHub Actions     ┌─── Tax Views
Tessie (Tesla) ────┼────────────────────────┤─── Monthly Reports
                   │      (Daily Sync)      └─── Schedule C Preview
Manual Bookings ───┘           │
                               ▼
                          Supabase
                         (Postgres)
```

## Database Schema

| Table | Purpose |
|-------|---------|
| `vehicles` | Vehicle info, purchase price, depreciation basis |
| `trips` | All trips from Tessie (tagged business/personal) |
| `charging_sessions` | Charging data with cost calculations |
| `bookings` | Turo reservations and revenue |
| `expense_intake` | Raw transactions from SimpleFIN |
| `expenses` | Categorized, allocated expenses |
| `revenue` | Income from Turo payouts |
| `depreciation_schedule` | Yearly depreciation tracking |

## Tax Calculation Views

- `ytd_business_use` - Business use percentage by year
- `expenses_allocated` - Expenses with business use allocation
- `tax_method_comparison` - Standard mileage vs actual expense comparison
- `charging_costs` - Monthly charging costs summary
- `pending_expenses` - Expenses awaiting categorization

## Setup

### 1. Run Setup Script

```bash
cd turo-cybertruck-ops
chmod +x setup.sh
./setup.sh
```

### 2. Add Anthropic API Key

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Create GitHub Repository

```bash
gh repo create turo-cybertruck-ops --private
git init
git add .
git commit -m "Initial setup"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/turo-cybertruck-ops.git
git push -u origin main
```

### 4. Add GitHub Secrets

Go to your repo → Settings → Secrets → Actions and add:

| Secret | Value |
|--------|-------|
| `SUPABASE_URL` | https://ycsdpcggyyitutsvplvd.supabase.co |
| `SUPABASE_SERVICE_KEY` | (from .env) |
| `TESSIE_API_TOKEN` | (from .env) |
| `CYBERTRUCK_VIN` | 7G2CEHEE6RA032607 |
| `VEHICLE_ID` | 63bd4029-46de-441a-b2dd-7bde67800d4e |
| `SIMPLEFIN_ACCESS_URL` | (from setup.sh output) |
| `ANTHROPIC_API_KEY` | (your key) |

## Manual Sync

Run syncs manually:

```bash
# Load environment
source .env

# Sync Tessie
python scripts/sync_tessie.py

# Sync SimpleFIN
python scripts/sync_simplefin.py

# Categorize expenses
python scripts/categorize_expenses.py
```

## Weekly Tasks

1. **Tag trips as business/personal** in Supabase Table Editor
2. **Review flagged expenses** (low confidence categorization)
3. **Add Turo bookings** manually until automation is added

## Tax Time Queries

Run these in Supabase SQL Editor:

```sql
-- YTD Business Use Percentage
SELECT * FROM ytd_business_use WHERE tax_year = 2025;

-- Standard Mileage vs Actual Expense
SELECT * FROM tax_method_comparison WHERE tax_year = 2025;

-- Expenses by Category
SELECT category, SUM(deductible_amount) 
FROM expenses_allocated 
WHERE tax_year = 2025 
GROUP BY category;

-- Total Revenue
SELECT SUM(amount) FROM revenue 
WHERE EXTRACT(YEAR FROM transaction_date) = 2025;
```

## Section 179 Notes

Your Cybertruck Cyberbeast qualifies as a "heavy vehicle" (GVWR > 6,000 lbs):
- **GVWR**: 6,843 lbs
- **Purchase Price**: $86,514.85
- **Potential Deduction**: Up to 100% of business use portion in year 1

Consult a tax professional for your specific situation.

## Costs

| Service | Cost |
|---------|------|
| Supabase | $0 (free tier) |
| SimpleFIN | $15/year |
| Tessie | $50/year |
| GitHub Actions | $0 (free tier) |
| Anthropic API | ~$1-2/month |
| **Total** | **~$80/year** |

## Support

For issues, open a GitHub issue or contact your Turo operations manager (Claude).
