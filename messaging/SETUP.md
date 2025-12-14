# Turo Messaging System - Setup Guide

## Overview

This system automatically:
1. Monitors Gmail for new Turo message notifications
2. Uses Claude AI to draft responses
3. Sends you a notification (via ntfy app) with the proposed response
4. You approve, edit, or deny - then manually paste to Turo

## Setup Steps

### Step 1: Install ntfy App (5 minutes)

**ntfy** is a free push notification service - much simpler than Signal for this use case.

1. **Install the app:**
   - iOS: https://apps.apple.com/app/ntfy/id1625396347
   - Android: https://play.google.com/store/apps/details?id=io.heckel.ntfy

2. **Subscribe to your topic:**
   - Open the app
   - Tap "+" to add a subscription
   - Enter topic: `turo-aether-messages` (or choose your own)
   - Save

3. **Add to GitHub Secrets:**
   - Go to your repo → Settings → Secrets → Actions
   - Add: `NTFY_TOPIC` = `turo-aether-messages`

That's it for notifications! You'll receive push notifications when guests message you.

---

### Step 2: Set Up Gmail API (15 minutes)

This lets the system read your Turo notification emails.

#### 2a. Create Google Cloud Project

1. Go to: https://console.cloud.google.com/
2. Create a new project: "Turo Message Bot"
3. Enable the Gmail API:
   - Go to "APIs & Services" → "Enable APIs"
   - Search "Gmail API" → Enable

#### 2b. Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User type: External
   - App name: "Turo Message Bot"
   - Add your email as a test user
4. Create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "Turo Bot"
5. Download the JSON file

#### 2c. Get Initial Token (one-time, on your Mac)

```bash
cd /Users/kurultai/turo-cybertruck-ops

# Install dependencies
pip install google-auth google-auth-oauthlib google-api-python-client

# Save your downloaded credentials
mv ~/Downloads/client_secret_*.json messaging/config/gmail_credentials.json

# Run the auth flow
python -c "
from messaging.scripts.check_gmail import get_gmail_service
get_gmail_service()
print('✓ Gmail authenticated!')
"
```

This will open a browser to authorize. After authorizing, a token file is saved.

#### 2d. Add to GitHub Secrets

```bash
# Encode credentials for GitHub
cat messaging/config/gmail_credentials.json | base64 | pbcopy
```
→ Add as `GMAIL_CREDENTIALS` secret

```bash
# Encode token for GitHub
cat messaging/state/gmail_token.pickle | base64 | pbcopy
```
→ Add as `GMAIL_TOKEN` secret

---

### Step 3: Test Locally (5 minutes)

```bash
cd /Users/kurultai/turo-cybertruck-ops
source .env

# Test the response generator
python messaging/scripts/generate_response.py

# Test notifications
python messaging/scripts/send_notification.py

# Run full workflow (will check Gmail)
python messaging/scripts/workflow.py
```

---

### Step 4: Enable GitHub Actions

Add these secrets to your repo (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `GMAIL_CREDENTIALS` | Base64-encoded gmail_credentials.json |
| `GMAIL_TOKEN` | Base64-encoded gmail_token.pickle |
| `NTFY_TOPIC` | `turo-aether-messages` |
| `ANTHROPIC_API_KEY` | (already set) |

Then push your changes:
```bash
git add .
git commit -m "Add Turo messaging system"
git push
```

The workflow will run:
- Every 5 minutes during daytime (6 AM - 6 PM EST)
- Every 15 minutes overnight

---

## How It Works

### When a Guest Messages You:

1. **Turo sends email** → Your Gmail
2. **GitHub Action runs** → Checks Gmail every 5 min
3. **AI drafts response** → Using your policies & FAQ
4. **You get a notification:**

```
🚗 NEW TURO MESSAGE

From: John D.
Trip: Dec 20-23, 2025

MESSAGE:
"Does it come with FSD?"

PROPOSED RESPONSE:
"Hi John! Yes, FSD is included..."

Reply: SEND / DENY / or edit
```

5. **You respond in the app** (or ignore)
6. **Manually paste to Turo** (MVP - no automation risk)

---

## Responding to Notifications

The ntfy app doesn't support two-way communication for free.

**For MVP:** When you see a good response, just:
1. Open Turo app
2. Go to the conversation
3. Copy the proposed response (long-press in ntfy)
4. Paste and send

**Future enhancement:** Could add Telegram bot for two-way approval, or build a simple web UI.

---

## Customizing Responses

Edit these files to adjust AI behavior:

| File | Purpose |
|------|---------|
| `messaging/config/vehicle_info.md` | Cybertruck specs & features |
| `messaging/config/policies.md` | Your rental policies |
| `messaging/config/faq.md` | Common Q&A |
| `messaging/config/tone_guide.md` | Communication style |

---

## Troubleshooting

### "No new messages found"
- Check Gmail for Turo emails
- Verify email notifications are enabled in Turo settings
- Check `messaging/state/processed_emails.json` - might already be processed

### "Gmail authentication failed"
- Re-run the local auth flow
- Update GMAIL_TOKEN secret with new token

### "Notification not received"
- Check ntfy app is subscribed to correct topic
- Test manually: `curl -d "test" ntfy.sh/turo-aether-messages`

### "Response quality is poor"
- Update FAQ with more examples
- Add common questions you receive
- Adjust tone_guide.md

---

## Cost

| Component | Cost |
|-----------|------|
| Gmail API | Free |
| ntfy | Free |
| Claude API | ~$0.02-0.05 per response |
| GitHub Actions | Free (under 2000 min/mo) |
| **Total** | **~$1-2/month** |

---

## Security Notes

- Gmail credentials are stored as encrypted GitHub Secrets
- Token is cached but can be revoked anytime in Google settings
- ntfy topics are public by default - use a random topic name if concerned
- No Turo credentials are stored - you manually paste responses

---

*Questions? The AI context files contain all your policies, so responses should be accurate. Adjust the files as your policies change.*
