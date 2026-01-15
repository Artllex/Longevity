from __future__ import annotations

import calendar
import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

# =========================
# OUTPUT TYPES
# =========================


@dataclass(frozen=True)
class DayItem:
    supplement_id: str
    name: str
    timing_hint: str | None  # "morning"|"any"|"evening"|None
    priority: int
    dose: dict | None


@dataclass(frozen=True)
class DayPlan:
    day: date
    block_id: str
    block_name: str
    items: list[DayItem]
    events: list[str]
    is_off_week: bool
    is_pulse_day: bool


# =========================
# UTILS
# =========================


def _ensure(condition: bool, msg: str):
    if not condition:
        raise ValueError(msg)


def _weekday_index(d: date) -> int:
    return d.weekday()  # Mon=0..Sun=6


def _weeks_between(anchor: date, d: date) -> int:
    return (d - anchor).days // 7


def _month_days(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _to_sorted_list(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, list):
        return sorted(x)
    if isinstance(x, set):
        return sorted(list(x))
    return x


# =========================
# MODEL ASSEMBLY
# =========================


def assemble_model_from_globals(spec_module) -> dict[str, Any]:
    """
    spec_module: np. import spec; podajesz moduł.
    Zwraca M_raw jako jeden słownik dla generatora.
    """
    return {
        "PIPELINE": spec_module.PIPELINE,
        "CONFIG": spec_module.CONFIG,
        "BLOCK_CALENDAR": spec_module.BLOCK_CALENDAR,
        "BLOCKS": spec_module.BLOCKS,
        "CORE_SET": spec_module.CORE_SET,
        "CONFLICTS": spec_module.CONFLICTS,
        "GLOBAL_EXCEPTIONS": spec_module.GLOBAL_EXCEPTIONS,
        "EVENTS": spec_module.EVENTS,
        "SUPPLEMENTS": spec_module.SUPPLEMENTS,
        "VALIDATION": spec_module.VALIDATION,
        "NORMALIZATION_RULES": spec_module.NORMALIZATION_RULES,
    }


# =========================
# VALIDATION + NORMALIZATION
# =========================


def validate_model(M: dict[str, Any]) -> None:
    required_top = [
        "PIPELINE",
        "CONFIG",
        "BLOCK_CALENDAR",
        "BLOCKS",
        "CORE_SET",
        "CONFLICTS",
        "GLOBAL_EXCEPTIONS",
        "EVENTS",
        "SUPPLEMENTS",
        "VALIDATION",
        "NORMALIZATION_RULES",
    ]
    for k in required_top:
        _ensure(k in M, f"Missing top-level key: {k}")

    id_re = re.compile(M["VALIDATION"]["ids"]["supplement_id_format"])
    for sid in M["SUPPLEMENTS"].keys():
        _ensure(
            id_re.match(sid) is not None,
            f"Invalid supplement_id format: {sid}",
        )

    for m in M["BLOCK_CALENDAR"].keys():
        _ensure(1 <= int(m) <= 12, f"BLOCK_CALENDAR invalid month key: {m}")
    for m, b in M["BLOCK_CALENDAR"].items():
        _ensure(
            b in M["BLOCKS"],
            f"BLOCK_CALENDAR references unknown block: month={m} block={b}",
        )

    for sid in M["CORE_SET"]:
        _ensure(
            sid in M["SUPPLEMENTS"],
            f"CORE_SET references missing supplement_id: {sid}",
        )

    # event_override ids exist
    for ev_id, ev in M["EVENTS"].items():
        override_id = ev.get("override_id")
        _ensure(
            override_id in M["CONFLICTS"]["event_overrides"],
            f"EVENTS[{ev_id}].override_id not found in "
            f"CONFLICTS.event_overrides: {override_id}",
        )

    # event_only schedule rules reference existing event
    for sid, spec in M["SUPPLEMENTS"].items():
        for r in spec.get("schedule_rules", []):
            if r["type"] == "event_only":
                ev_id = r["params"]["event_id"]
                _ensure(
                    ev_id in M["EVENTS"],
                    f"{sid} event_only references unknown event_id: {ev_id}",
                )

    # pipeline exact match (jeśli ustawione)
    must_equal = M["VALIDATION"]["consistency"].get("pipeline_must_equal")
    if must_equal:
        _ensure(
            M["PIPELINE"] == must_equal,
            f"PIPELINE must equal {must_equal} but is {M['PIPELINE']}",
        )


def normalize_model(M: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizacja BEZ mutowania M wejściowego.
    (shallow-copy top-level + kopie poddrzew, które dotykamy)
    """
    N: dict[str, Any] = dict(M)

    # Copy subtrees we mutate
    N["SUPPLEMENTS"] = {k: dict(v) for k, v in M["SUPPLEMENTS"].items()}
    N["EVENTS"] = {k: dict(v) for k, v in M["EVENTS"].items()}
    N["CONFLICTS"] = dict(M["CONFLICTS"])

    # CORE_SET -> list (opcjonalnie deterministycznie)
    if isinstance(N["CORE_SET"], set):
        N["CORE_SET"] = sorted(list(N["CORE_SET"]))

    # Normalize SUPPLEMENTS internals
    for sid, spec in list(N["SUPPLEMENTS"].items()):
        spec2 = dict(spec)

        # constraints
        cons2 = []
        for c in spec2.get("constraints", []):
            c2 = dict(c)
            params = dict(c2.get("params", {}))
            if "blocks" in params:
                params["blocks"] = _to_sorted_list(params["blocks"])
            if "supplement_ids" in params:
                params["supplement_ids"] = _to_sorted_list(
                    params["supplement_ids"]
                )
            if "months_included" in params:
                params["months_included"] = _to_sorted_list(
                    params["months_included"]
                )
            c2["params"] = params
            cons2.append(c2)
        spec2["constraints"] = cons2

        # schedule_rules
        rules2 = []
        for r in spec2.get("schedule_rules", []):
            r2 = dict(r)
            r2["active_blocks"] = _to_sorted_list(r2.get("active_blocks"))
            params = dict(r2.get("params", {}))
            if "days_included" in params:
                params["days_included"] = _to_sorted_list(
                    params["days_included"]
                )
            if "fixed_days" in params:
                params["fixed_days"] = _to_sorted_list(params["fixed_days"])
            r2["params"] = params
            rules2.append(r2)
        spec2["schedule_rules"] = rules2

        N["SUPPLEMENTS"][sid] = spec2

    # Normalize EVENTS months
    for _, ev in N["EVENTS"].items():
        if isinstance(ev.get("months"), set):
            ev["months"] = sorted(list(ev["months"]))

    return N


# =========================
# EVENT RESOLUTION
# =========================


def _event_days_for_month(
    M: dict[str, Any], year: int, month: int, event: dict[str, Any]
) -> list[date]:
    cfg = M["CONFIG"]["event_day_selection"]["pulse"]
    mapping = cfg["month_week_selection_mapping"]

    mdays = _month_days(year, month)
    days = mapping.get(event["month_week_selection"], [])
    desired_len = int(event["length_days"])

    resolved: list[date] = []
    for dday in days[:desired_len]:
        if 1 <= dday <= mdays:
            resolved.append(date(year, month, dday))
        else:
            # fallback
            if cfg.get("fallback_if_day_invalid") == "next_valid_day_in_month":
                resolved.append(date(year, month, mdays))
            else:
                raise ValueError(f"Invalid day {dday} for {year}-{month}")

    # BONUS: dedupe while preserving order
    resolved = list(dict.fromkeys(resolved))
    _ensure(
        len(resolved) > 0,
        f"No event days resolved for event={event.get('id')} month={month}",
    )

    # BONUS: ensure length by filling next days if possible
    while len(resolved) < desired_len:
        last_day = resolved[-1]
        if last_day.day >= mdays:
            break
        resolved.append(last_day + timedelta(days=1))

    return resolved[:desired_len]


def active_events_on_day(M: dict[str, Any], d: date) -> list[str]:
    evs: list[str] = []
    for ev_id, ev in M["EVENTS"].items():
        if ev["type"] == "pulse" and d.month in ev["months"]:
            days = _event_days_for_month(M, d.year, d.month, ev)
            if d in days:
                evs.append(ev_id)
    evs.sort(
        key=lambda e: int(M["EVENTS"][e].get("priority", 0)), reverse=True
    )
    return evs


# =========================
# PIPELINE STEPS
# =========================


def base_by_block(M: dict[str, Any], d: date, block_id: str) -> set[str]:
    return set(M["CORE_SET"])  # CORE daily (can be removed by OFF WEEK)


def apply_schedule_rules(
    M: dict[str, Any],
    d: date,
    block_id: str,
    current: set[str],
    flags: dict[str, bool],
    cycle_anchor_date: date | None,
) -> set[str]:
    wd = _weekday_index(d)

    def blocks_ok(active_blocks: list[str] | None) -> bool:
        if active_blocks is None:
            return True
        return block_id in active_blocks

    for sid, spec in M["SUPPLEMENTS"].items():
        for rule in spec.get("schedule_rules", []):
            rtype = rule["type"]
            ab = rule.get("active_blocks")
            if not blocks_ok(ab):
                continue

            params = rule.get("params", {})

            if rtype == "daily":
                current.add(sid)

            elif rtype == "week_pattern":
                if wd in params["days_included"]:
                    current.add(sid)

            elif rtype == "times_per_week":
                if params.get("weekdays_only") and wd >= 5:
                    continue
                if wd in params["fixed_days"]:
                    current.add(sid)

            elif rtype == "cycle_weeks":
                align = params.get("alignment", "custom_date")
                if align == "year_start":
                    anchor = date(d.year, 1, 1)
                elif align == "custom_date":
                    _ensure(
                        cycle_anchor_date is not None,
                        "cycle_anchor_date required for custom_date "
                        "cycle_weeks",
                    )
                    assert cycle_anchor_date is not None
                    anchor = cycle_anchor_date
                else:
                    raise ValueError(f"Unknown alignment: {align}")

                on_w = int(params["on_weeks"])
                off_w = int(params["off_weeks"])
                period = on_w + off_w
                w = _weeks_between(anchor, d) % period
                if w < on_w:
                    current.add(sid)

            elif rtype == "optional":
                if flags.get(params["flag"], False):
                    current.add(sid)

            elif rtype == "event_only":
                # handled in apply_events
                pass

            else:
                raise ValueError(f"Unknown schedule rule type: {rtype}")

    return current


def apply_constraints(
    M: dict[str, Any], d: date, block_id: str, current: set[str]
) -> set[str]:
    # fixed-point because require_supplements can add items
    changed = True
    while changed:
        changed = False
        for sid in list(current):
            spec = M["SUPPLEMENTS"][sid]
            for c in spec.get("constraints", []):
                ctype = c["type"]
                params = c.get("params", {})

                if ctype == "allowed_blocks":
                    if block_id not in params["blocks"]:
                        current.discard(sid)

                elif ctype == "exclude_blocks":
                    if block_id in params["blocks"]:
                        current.discard(sid)

                elif ctype == "seasonal":
                    if d.month not in params["months_included"]:
                        current.discard(sid)

                elif ctype == "exclude_supplements":
                    # if this supplement is present, drop the forbidden ones
                    if sid in current:
                        for x in params["supplement_ids"]:
                            current.discard(x)

                elif ctype == "require_supplements":
                    if sid in current:
                        for req in params["supplement_ids"]:
                            if req not in current:
                                current.add(req)
                                changed = True

                else:
                    raise ValueError(f"Unknown constraint type: {ctype}")

    return current


def apply_supplement_exclusions(
    M: dict[str, Any], current: set[str]
) -> set[str]:
    excl = M["CONFLICTS"]["supplement_exclusions"]
    for a, bs in excl.items():
        if a in current:
            for b in bs:
                current.discard(b)
    return current


def apply_block_exclusions(
    M: dict[str, Any], block_id: str, current: set[str]
) -> set[str]:
    block_excl = M["CONFLICTS"]["block_exclusions"].get(block_id, set())
    for sid in list(current):
        if sid in block_excl:
            current.discard(sid)
    return current


def apply_events(
    M: dict[str, Any], d: date, current: set[str], events: list[str]
) -> set[str]:
    # Add event_only supplements if their event is active
    active_event_set = set(events)
    for sid, spec in M["SUPPLEMENTS"].items():
        for rule in spec.get("schedule_rules", []):
            if rule["type"] == "event_only":
                ev_id = rule["params"]["event_id"]
                if ev_id in active_event_set:
                    current.add(sid)

    # Apply overrides in priority order
    for ev_id in events:
        override_id = M["EVENTS"][ev_id]["override_id"]
        override = M["CONFLICTS"]["event_overrides"][override_id]
        effect = override["effect"]

        if effect == "allow_only":
            allowed = set(override["allowed_set"])
            current = current.intersection(allowed)

        elif effect == "remove_all":
            current = set()

        else:
            raise ValueError(f"Unknown override effect: {effect}")

    return current


def apply_global_exceptions(
    M: dict[str, Any],
    d: date,
    current: set[str],
    events: list[str],
    off_week_start_date: date | None,
    off_week_week_of_year: int | None,
) -> set[str]:
    for ex in M["GLOBAL_EXCEPTIONS"]:
        if ex["type"] != "off_week":
            continue

        in_off = False
        if off_week_start_date is not None:
            start = off_week_start_date
            end = start + timedelta(days=int(ex["duration_days"]) - 1)
            in_off = start <= d <= end
        elif off_week_week_of_year is not None:
            raise NotImplementedError(
                "off_week_week_of_year not implemented; "
                "use off_week_start_date"
            )

        if in_off:
            forbidden = set(ex.get("hard_exclusion_of_events", set()))
            overlap = forbidden.intersection(set(events))
            _ensure(
                len(overlap) == 0,
                f"OFF WEEK overlaps forbidden events: {overlap}",
            )

            if ex["effect"] == "remove_all":
                return set()
            raise ValueError(
                f"Unknown GLOBAL_EXCEPTIONS effect: {ex['effect']}"
            )

    return current


# =========================
# FINAL ASSEMBLY
# =========================


def _items_from_ids(M: dict[str, Any], ids: set[str]) -> list[DayItem]:
    items: list[DayItem] = []
    for sid in ids:
        spec = M["SUPPLEMENTS"][sid]
        dose = spec.get("default_dose")
        timing = dose.get("timing_hint") if isinstance(dose, dict) else None
        items.append(
            DayItem(
                supplement_id=sid,
                name=spec.get("name", sid),
                timing_hint=timing,
                priority=int(spec.get("priority", 0)),
                dose=dose,
            )
        )
    return items


def _sort_items(M: dict[str, Any], items: list[DayItem]) -> list[DayItem]:
    order = M["NORMALIZATION_RULES"]["ordering"]["timing_hint_order"]
    timing_rank = {v: i for i, v in enumerate(order)}

    def key(it: DayItem):
        tr = timing_rank.get(it.timing_hint, len(order))
        return (tr, -it.priority, it.supplement_id)

    return sorted(items, key=key)


def generate_year_plan(
    M_raw: dict[str, Any],
    year: int,
    *,
    off_week_start_date: date | None = None,
    off_week_week_of_year: int | None = None,
    cycle_anchor_date: date | None = None,
    flags: dict[str, bool] | None = None,
) -> list[DayPlan]:
    flags = flags or {}

    validate_model(M_raw)
    M = normalize_model(M_raw)

    if off_week_start_date is not None:
        _ensure(
            off_week_start_date.weekday() == 0,
            "off_week_start_date must be a Monday (weekday=0)",
        )

    plans: list[DayPlan] = []
    d = date(year, 1, 1)
    last = date(year, 12, 31)

    while d <= last:
        block_id = M["BLOCK_CALENDAR"][d.month]
        events = active_events_on_day(M, d)

        block_name = M["BLOCKS"][block_id].get("name", block_id)
        is_pulse_day = len(events) > 0

        # pipeline
        current = base_by_block(M, d, block_id)
        current = apply_schedule_rules(
            M, d, block_id, current, flags, cycle_anchor_date
        )
        current = apply_constraints(M, d, block_id, current)
        current = apply_supplement_exclusions(M, current)
        current = apply_block_exclusions(M, block_id, current)
        current = apply_events(M, d, current, events)
        current = apply_global_exceptions(
            M, d, current, events, off_week_start_date, off_week_week_of_year
        )
        # OFF WEEK = remove_all -> pusta lista
        is_off_week = (len(current) == 0) and (not is_pulse_day)

        items = _sort_items(M, _items_from_ids(M, current))
        plans.append(
            DayPlan(
                day=d,
                block_id=block_id,
                block_name=block_name,
                items=items,
                events=events,
                is_off_week=is_off_week,
                is_pulse_day=is_pulse_day,
            )
        )

        d += timedelta(days=1)

    return plans


# =========================
# CSV
# =========================


def export_csv(plans, path: str) -> None:
    """
    CSV: 1 wiersz = 1 dzień
    Kolumny: date, block, events, morning, any, evening
    W komórkach: lista "name (dose)" rozdzielona " | "
    """

    def fmt_item(it) -> str:
        # it: DayItem from engine
        dose = it.dose
        if isinstance(dose, dict):
            amt = dose.get("amount")
            unit = dose.get("unit")
            if amt is not None or unit is not None:
                return f"{it.name} ({amt} {unit})".strip()
        return f"{it.name}"

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "block", "events", "morning", "any", "evening"])

        for p in plans:
            buckets = {"morning": [], "any": [], "evening": [], None: []}
            for it in p.items:
                buckets.get(it.timing_hint, buckets[None]).append(fmt_item(it))

            # 'any' + None można zlać do "any" jeśli chcesz;
            # tu trzymam rozdzielnie: None -> any
            any_items = buckets["any"] + buckets[None]

            w.writerow(
                [
                    p.day.isoformat(),
                    p.block_id,
                    ",".join(p.events),
                    " | ".join(buckets["morning"]),
                    " | ".join(any_items),
                    " | ".join(buckets["evening"]),
                ]
            )


# =========================
# ICS
# =========================


def _ics_escape(s: str) -> str:
    # RFC5545 basic escaping for TEXT
    return (
        s.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )


def _dtstamp_utc() -> str:
    # DTSTAMP in UTC, format: YYYYMMDDTHHMMSSZ
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _uid_for_day(prefix: str, d: date) -> str:
    # stable UID per day, deterministic
    h = hashlib.sha1(f"{prefix}:{d.isoformat()}".encode()).hexdigest()[:16]
    return f"{prefix}-{d.strftime('%Y%m%d')}-{h}@longevity"


def _format_day_items_for_desc(items) -> tuple[str, str, str]:
    """
    Returns 3 lines: morning/any/evening as bullet-like text (no markdown)
    """

    def fmt(it) -> str:
        dose = it.dose
        if isinstance(dose, dict):
            amt = dose.get("amount")
            unit = dose.get("unit")
            if amt is not None or unit is not None:
                return f"{it.name} ({amt} {unit})".strip()
        return it.name

    morning = [fmt(it) for it in items if it.timing_hint == "morning"]
    evening = [fmt(it) for it in items if it.timing_hint == "evening"]
    any_ = [
        fmt(it) for it in items if it.timing_hint not in ("morning", "evening")
    ]

    line_m = "MORNING: " + (" | ".join(morning) if morning else "-")
    line_a = "ANY: " + (" | ".join(any_) if any_ else "-")
    line_e = "EVENING: " + (" | ".join(evening) if evening else "-")
    return line_m, line_a, line_e


def export_ics(
    plans,
    path: str,
    *,
    calendar_name: str = "Longevity 4.8",
    uid_prefix: str = "longevity48",
    include_empty_days: bool = True,
) -> None:
    """
    ICS: VEVENT per day (all-day event).
    Summary zawiera blok + ewentualnie eventy (np. Fisetin).
    Description: rozpiska morning/any/evening.
    """
    dtstamp = _dtstamp_utc()

    lines: list[str] = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//Longevity 4.8//Schedule//EN")
    lines.append("CALSCALE:GREGORIAN")
    lines.append(f"X-WR-CALNAME:{_ics_escape(calendar_name)}")

    for p in plans:
        if (
            (not include_empty_days)
            and (len(p.items) == 0)
            and (len(p.events) == 0)
        ):
            continue

        # all-day event: DTSTART=DATE, DTEND=DATE(next day)
        d0 = p.day.strftime("%Y%m%d")
        d1 = (p.day + timedelta(days=1)).strftime("%Y%m%d")

        uid = _uid_for_day(uid_prefix, p.day)

        # SUMMARY
        # przykład: "NAD" / "DETOX • Fisetin"
        ev_label = ""
        if p.events:
            ev_label = " • " + " & ".join(p.events)
        summary = f"{p.block_id}{ev_label}"

        # DESCRIPTION
        if len(p.items) == 0:
            desc = "OFF/EMPTY DAY"
        else:
            m, a, e = _format_day_items_for_desc(p.items)
            desc = "\n".join([m, a, e])

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{dtstamp}")
        lines.append(f"DTSTART;VALUE=DATE:{d0}")
        lines.append(f"DTEND;VALUE=DATE:{d1}")
        lines.append(f"SUMMARY:{_ics_escape(summary)}")
        lines.append(f"DESCRIPTION:{_ics_escape(desc)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    # Fold lines to 75 octets? Większość klientów działa bez tego,
    # ale lepiej zwinąć.
    folded = _ics_fold_lines(lines)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(folded) + "\n")


def _ics_fold_lines(lines: list[str]) -> list[str]:
    """
    RFC5545 line folding: max 75 octets; kontynuacja zaczyna się spacją.
    Tu liczymy w przybliżeniu po długości znaków
    (UTF-8 może różnić się w octetach),
    ale w praktyce dla większości klientów jest OK.
    """
    out: list[str] = []
    for line in lines:
        if len(line) <= 75:
            out.append(line)
            continue
        # fold
        s = line
        out.append(s[:75])
        s = s[75:]
        while s:
            out.append(" " + s[:74])
            s = s[74:]
    return out
