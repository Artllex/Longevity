from __future__ import annotations

import os
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from . import spec
from .engine import DayPlan, assemble_model_from_globals, generate_year_plan


def _bucket_items(p: DayPlan) -> dict[str, list[str]]:
    def fmt(it) -> str:
        dose = it.dose
        if isinstance(dose, dict):
            amt = dose.get("amount")
            unit = dose.get("unit")
            if amt is not None or unit is not None:
                return f"{it.name} ({amt} {unit})".strip()
        return it.name

    buckets = {"morning": [], "any": [], "evening": []}
    for it in p.items:
        if it.timing_hint == "morning":
            buckets["morning"].append(fmt(it))
        elif it.timing_hint == "evening":
            buckets["evening"].append(fmt(it))
        else:
            buckets["any"].append(fmt(it))
    return buckets


def build_email_text(p: DayPlan) -> str:
    b = _bucket_items(p)
    ev = ", ".join(p.events) if p.events else "-"

    lines = []
    lines.append(f"DATA: {p.day.isoformat()}")
    lines.append(f"MODUŁ: {p.block_id}")
    lines.append(f"EVENTY: {ev}")
    lines.append("")
    lines.append("RANO:")
    lines.extend([f"- {x}" for x in b["morning"]] or ["- (brak)"])
    lines.append("")
    lines.append("W CIĄGU DNIA:")
    lines.extend([f"- {x}" for x in b["any"]] or ["- (brak)"])
    lines.append("")
    lines.append("WIECZÓR:")
    lines.extend([f"- {x}" for x in b["evening"]] or ["- (brak)"])
    return "\n".join(lines)


def send_email_smtp(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    to_email: str,
    subject: str,
    body: str,
    use_tls: bool = True,
) -> None:
    print(
        f"[mailer] connecting to {smtp_host}:{smtp_port} as {smtp_user} -> {to_email}",
        flush=True,
    )

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if use_tls:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
            s.set_debuglevel(1)
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(smtp_user, smtp_password)
            s.send_message(msg)
    else:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as s:
            s.login(smtp_user, smtp_password)
            s.send_message(msg)

    print("[mailer] sent", flush=True)


def main():
    print("Mailer start")

    # pokaż, czy env w ogóle jest ustawiony
    for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "TZ"]:
        v = os.environ.get(k)
        if v is None:
            print(f"ENV {k}=<MISSING>")
        elif k == "SMTP_PASS":
            print(f"ENV {k}=<SET len={len(v)}>")
        else:
            print(f"ENV {k}={v}")

    # 1) plan
    M_raw = assemble_model_from_globals(spec)

    target = datetime.now(ZoneInfo("Europe/Warsaw")).date()

    plans = generate_year_plan(
        M_raw,
        target.year,
        off_week_start_date=date(target.year, 2, 2),
        cycle_anchor_date=date(target.year, 1, 6),
        flags={"enable_melissa": True},
    )

    print("Target date:", target.isoformat())
    print(
        "Plans range:",
        plans[0].day.isoformat(),
        "->",
        plans[-1].day.isoformat(),
    )

    p = next((x for x in plans if x.day == target), None)
    print("Found day:", p is not None)

    if p is None:
        raise RuntimeError(
            "Target day not found in generated plans (year mismatch?)"
        )

    body = build_email_text(p)
    subject = f"Longevity 4.8 — {p.day.isoformat()} ({p.block_id})"
    print("Subject:", subject)
    print("Body preview:", body[:120].replace("\n", " | "), "...")

    send_email_smtp(
        smtp_host=os.environ["SMTP_HOST"],
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_user=os.environ["SMTP_USER"],
        smtp_password=os.environ["SMTP_PASS"],
        to_email="arkadiusz.pajda.97@onet.pl",
        subject=subject,
        body=body,
        use_tls=True,
    )

    print("✅ Sent")


if __name__ == "__main__":
    main()
    print("Done.")
