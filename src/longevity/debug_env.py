import os

KEYS = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "TZ"]

for k in KEYS:
    v = os.environ.get(k)
    if v is None:
        print(f"{k}=<MISSING>")
    else:
        safe = v if k not in {"SMTP_PASS"} else f"<SET len={len(v)}>"
        print(f"{k}={safe}")
