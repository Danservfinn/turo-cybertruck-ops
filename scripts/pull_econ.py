import base64
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

secret = os.environ["SIMPLEFIN_ACCESS_URL"].strip()

# Strip any scheme, then split creds@host[:port][/path]
body = re.sub(r"^https?://", "", secret)
if "@" in body:
    creds, rest = body.rsplit("@", 1)
else:
    creds, rest = "", body
parts = rest.split("/", 1)
hostport = parts[0]
path = "/" + parts[1] if len(parts) > 1 else "/simplefin/accounts"

base = f"https://{hostport}{path}"
headers = {}
if creds:
    token = base64.b64encode(creds.encode()).decode()
    headers["Authorization"] = "Basic " + token

start = datetime.now(timezone.utc) - timedelta(days=400)
sep = "&" if "?" in base else "?"
url = base + sep + urllib.parse.urlencode({"start-date": int(start.timestamp())})
print("host:", hostport)

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.load(r)

out = []
for acct in data.get("accounts", []):
    for t in acct.get("transactions", []):
        desc = t.get("description", "")
        if any(k in desc.lower() for k in ("turo", "tesla", "ally", "insurance", "geico")):
            posted = t.get("posted")
            d = datetime.fromtimestamp(posted, tz=timezone.utc).date().isoformat() if posted else None
            out.append({"date": d, "desc": desc[:80], "amount": float(t.get("amount", 0))})
out.sort(key=lambda x: x["date"] or "")
print(f"matched: {len(out)} transactions")
with open("turo-econ.json", "w") as f:
    json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "txns": out}, f, indent=1)
