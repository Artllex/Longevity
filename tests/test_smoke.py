from datetime import date

from longevity import spec
from longevity.engine import assemble_model_from_globals, generate_year_plan


def test_generate_plan_smoke() -> None:
    M = assemble_model_from_globals(spec)
    plans = generate_year_plan(
        M,
        2026,
        off_week_start_date=date(2026, 2, 2),  # poniedziałek
        cycle_anchor_date=date(2026, 1, 1),
    )
    assert len(plans) == 365
