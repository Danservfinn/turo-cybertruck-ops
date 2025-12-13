#!/bin/bash
# Setup script for Turo Cybertruck Ops

echo "================================================"
echo "Turo Cybertruck Operations Setup"
echo "================================================"

# Step 1: Claim SimpleFIN Access URL
echo ""
echo "Step 1: Claiming SimpleFIN Access URL..."
SIMPLEFIN_SETUP_TOKEN="aHR0cHM6Ly9iZXRhLWJyaWRnZS5zaW1wbGVmaW4ub3JnL3NpbXBsZWZpbi9jbGFpbS9CRkU1MDFGMkZGOEI1NzJBRDI0NUFBOTZEQjUyMDlBREYyNzVCMkE5NjdFMDIzMUQ1NjUxNjU2REQyRDVCOTBBQzJGNjRBN0IxMjdEOTNCODRBREIxQkU2MDMxNkQ4RjMwOTI4MDZEOUE4NjYwQUIyRjkxMjBBOTE2RkUwMzRCOQ=="

CLAIM_URL=$(echo "$SIMPLEFIN_SETUP_TOKEN" | base64 -d)
echo "Claim URL: $CLAIM_URL"

SIMPLEFIN_ACCESS_URL=$(curl -s -X POST "$CLAIM_URL")

if [ -z "$SIMPLEFIN_ACCESS_URL" ] || [[ "$SIMPLEFIN_ACCESS_URL" == *"error"* ]]; then
    echo "⚠️  Warning: Could not claim SimpleFIN token."
    echo "   The token may have already been claimed."
    echo "   You'll need to generate a new setup token from SimpleFIN."
    echo ""
    echo "   Go to: https://beta-bridge.simplefin.org"
    echo "   → My Accounts → Apps → New Connection"
    echo ""
    read -p "Enter your new SimpleFIN Access URL (or press Enter to skip): " SIMPLEFIN_ACCESS_URL
else
    echo "✓ SimpleFIN Access URL obtained!"
fi

echo ""
echo "================================================"
echo "Your credentials (save these!):"
echo "================================================"
echo ""
echo "SUPABASE_URL=https://ycsdpcggyyitutsvplvd.supabase.co"
echo "SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljc2RwY2dneXlpdHV0c3ZwbHZkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTY0NzAxMiwiZXhwIjoyMDgxMjIzMDEyfQ.jaSiGK3bg_jC1hslrp-uU_1Kt5mBm-d0uYZxbpryjuQ"
echo "TESSIE_API_TOKEN=IhWDh7ryyAYTkuGvkeE9I7kkV8gVBXnp"
echo "CYBERTRUCK_VIN=7G2CEHEE6RA032607"
echo "VEHICLE_ID=63bd4029-46de-441a-b2dd-7bde67800d4e"
echo "SIMPLEFIN_ACCESS_URL=$SIMPLEFIN_ACCESS_URL"
echo ""

# Step 2: Create .env file
echo "Step 2: Creating .env file..."
cat > .env << EOF
SUPABASE_URL=https://ycsdpcggyyitutsvplvd.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljc2RwY2dneXlpdHV0c3ZwbHZkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTY0NzAxMiwiZXhwIjoyMDgxMjIzMDEyfQ.jaSiGK3bg_jC1hslrp-uU_1Kt5mBm-d0uYZxbpryjuQ
TESSIE_API_TOKEN=IhWDh7ryyAYTkuGvkeE9I7kkV8gVBXnp
CYBERTRUCK_VIN=7G2CEHEE6RA032607
VEHICLE_ID=63bd4029-46de-441a-b2dd-7bde67800d4e
SIMPLEFIN_ACCESS_URL=$SIMPLEFIN_ACCESS_URL
ANTHROPIC_API_KEY=your_anthropic_api_key_here
EOF

echo "✓ Created .env file"
echo ""
echo "⚠️  IMPORTANT: Add your ANTHROPIC_API_KEY to .env"
echo "   Get one at: https://console.anthropic.com/settings/keys"
echo ""

# Step 3: Instructions for GitHub
echo "================================================"
echo "Step 3: GitHub Repository Setup"
echo "================================================"
echo ""
echo "1. Create a new GitHub repository:"
echo "   gh repo create turo-cybertruck-ops --private"
echo ""
echo "2. Add secrets to GitHub (Settings → Secrets → Actions):"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_SERVICE_KEY"
echo "   - TESSIE_API_TOKEN"
echo "   - CYBERTRUCK_VIN"
echo "   - VEHICLE_ID"
echo "   - SIMPLEFIN_ACCESS_URL"
echo "   - ANTHROPIC_API_KEY"
echo ""
echo "3. Push this code:"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial setup'"
echo "   git branch -M main"
echo "   git remote add origin <your-repo-url>"
echo "   git push -u origin main"
echo ""
echo "================================================"
echo "Setup complete! The workflow will run daily at 6 AM UTC."
echo "You can also trigger it manually in GitHub Actions."
echo "================================================"
