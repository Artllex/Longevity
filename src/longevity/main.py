from datetime import date

from longevity import spec
from longevity.engine import (
    assemble_model_from_globals,
    export_csv,
    generate_year_plan,
)

M_raw = assemble_model_from_globals(spec)

plans = generate_year_plan(
    M_raw,
    2026,
    off_week_start_date=date(2026, 2, 2),  # poniedziałek
    cycle_anchor_date=date(2026, 1, 6),
    flags={"enable_melissa": True},
)

# podgląd 1 dnia
p = plans[0]
print(p.day, p.block_id, p.events)
for it in p.items:
    print("-", it.supplement_id, it.timing_hint, it.priority)

# zapis CSV
export_csv(plans, "longevity_2026.csv")
print("CSV saved: longevity_2026.csv")
