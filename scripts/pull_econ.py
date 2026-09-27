import json, os, urllib.request, urllib.parse
import base64
from datetime import datetime, timedelta, timezone

secret = os.environ["SIMPLEFIN_ACCESS_URL"].strip()
HEADERS = {}
print("secret form:", "starts-http" if secret.startswith("http") else ("has-at" if "@" in secret else "raw-key"))

if secret.startswith("http"):
    base = secret
elif "@" in secret:
    # user:pass@host form; use https scheme with basic auth header
    creds, host = secret.rsplit("@", 1)
    base = "https://" + host
    auth = base64.b64encode(creds.encode()).decode()
    HEADERS = {"Authorization": "Basic " + auth}
else:
    req = urllib.request.Request(
        "https://beta-bridge.simplefin.org/simplefin/auth",
        data=secret.encode(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        base = r.read().decode().strip()

base = base.rstrip("/")
if not base.endswith("/accounts"):
    base = base + "/accounts"

start = datetime.now(timezone.utc) - timedelta(days=400)
sep = "&" if "?" in base else "?"
url = base + sep + urllib.parse.urlencode({"start-date": int(start.timestamp())})
print("fetching:", urllib.parse.urlsplit(url).netloc)

req = urllib.request.Request(url, headers=HEADERS)
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
