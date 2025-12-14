# Turo Message Response System - Architecture Proposal

> **Status:** Draft / Planning
> **Created:** December 13, 2025
> **Purpose:** AI-assisted Turo guest communication with human-in-the-loop approval via Signal

---

## Overview

```
TURO (Incoming) --> CLAUDE (Draft) --> SIGNAL (Approve) --> TURO (Send)
    Guest              AI generates      You review &       Response
    message            response          approve/edit       sent
```

---

## Workflow

### Step 1: Detect New Turo Message
**Challenge:** Turo has no official API

**Options:**

| Option | Pros | Cons | Recommended |
|--------|------|------|-------------|
| A. Email Parsing | Reliable, Turo sends notifications | Slight delay | YES |
| B. Browser Automation | Real-time | Fragile, ToS risk | Backup |
| C. Manual Forward | Simple | Requires your action | MVP |

### Step 2: Generate AI Response
Claude Opus 4.5 drafts response with context about vehicle, policies, FAQ.

### Step 3: Signal Approval
You receive message like:

```
NEW TURO MESSAGE

From: John D.
Trip: Dec 20-23

MESSAGE:
"Does it come with FSD?"

PROPOSED RESPONSE:
"Hi John! Yes, FSD is included..."

Reply: SEND / DENY / or type edited response
```

### Step 4: Send to Turo
Options: Browser automation, manual paste, or mobile deep link.

---

## Implementation Options

### Option A: MVP (Manual Send)
- Gmail watches for Turo emails
- Claude drafts response
- Signal sends for approval
- You manually paste to Turo

**Pros:** Simple, no ToS risk
**Cons:** Manual send step

### Option B: Fully Automated
- Same as above, plus Playwright sends to Turo

**Pros:** Hands-off
**Cons:** Complex, ToS gray area

---

## What I Need From You

1. **Which option?** A (MVP) or B (Automated)?
2. **Email provider?** Gmail or other?
3. **Signal number?** For approvals
4. **Hosting?** Your Mac, GitHub Actions, or cloud server?
5. **Your policies?** Pickup location, mileage limits, charging rules

---

## Cost Estimate

| Component | Cost |
|-----------|------|
| Gmail API | Free |
| Claude API | ~$0.02-0.05/response |
| Signal | Free |
| Server (if needed) | $5-10/mo |
| **Total** | **~$5-15/month** |

---

Ready to build when you answer the questions above!
