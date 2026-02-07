from __future__ import annotations

import os
import smtplib
from datetime import date, timedelta
from email.message import EmailMessage

from . import spec
from .engine import (
    DayItem,
    DayPlan,
    assemble_model_from_globals,
    generate_year_plan,
)


def _bucket_items(p: DayPlan) -> dict[str, list[str]]:
    def fmt(it: DayItem) -> str:
        dose = it.dose
        if isinstance(dose, dict):
            amt = dose.get("amount")
            unit = dose.get("unit")
            if amt is not None or unit is not None:
                return f"{it.name} ({amt} {unit})".strip()
        return it.name

    buckets: dict[str, list[str]] = {"morning": [], "any": [], "evening": []}
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
    events = list(p.events)
    if p.is_off_week:
        events = ["off_week"] + events
    ev = ", ".join(events) if events else "-"

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
    attachment_txt: tuple[str, str] | None = None,
    use_tls: bool = True,
) -> None:
    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_txt is not None:
        filename, content = attachment_txt
        msg.add_attachment(
            content.encode("utf-8"),
            maintype="text",
            subtype="plain",
            filename=filename,
        )

    if use_tls:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_password)
            s.send_message(msg)
    else:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as s:
            s.login(smtp_user, smtp_password)
            s.send_message(msg)


def build_30day_text(plans: list[DayPlan], start: date, days: int = 30) -> str:
    # Szybki lookup: date -> DayPlan
    by_day = {p.day: p for p in plans}
    chunks: list[str] = []

    for i in range(days):
        d = start + timedelta(days=i)
        p = by_day.get(d)
        if p is None:
            # jeśli coś poszło nie tak (np. inny rok), daj czytelną informację
            chunks.append(f"DATA: {d.isoformat()}\nBRAK PLANU DLA TEJ DATY\n")
            continue

        chunks.append(build_email_text(p))
        chunks.append("\n")  # dodatkowa pusta linia między dniami

    return "\n".join(chunks).strip() + "\n"


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
    plans = generate_year_plan(
        M_raw,
        2026,
        off_week_start_date=date(2026, 2, 2),
        cycle_anchor_date=date(2026, 1, 6),
        flags={"enable_melissa": True},
    )

    target = date.today()
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
    horizon_txt = build_30day_text(plans, target, days=30)
    attach_name = f"longevity_next_30_days_{target.isoformat()}.txt"
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
        attachment_txt=(attach_name, horizon_txt),
        use_tls=True,
    )

    print("✅ Sent")


if __name__ == "__main__":
    main()
    print("Done.")
