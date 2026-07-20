"""describe.py's pure logic — no simulation needed."""

from __future__ import annotations

import pandas as pd

from grocery_sim.describe import (
    _cap_first,
    _round_money,
    _round_pct,
    _shrinkage_rate,
    _task_type,
    pick_misguide_candidate,
)
from grocery_sim.params import PHASE5


def test_misguide_priority_competitor_first():
    assert pick_misguide_candidate({"competitor": "2026-06", "war": "2025-01"}) == "competitor"


def test_misguide_priority_war_over_hazard():
    assert pick_misguide_candidate(
        {"war": "2025-01", "operational_hazard": "2027-04"}
    ) == "war"

    assert pick_misguide_candidate({"operational_hazard": "2027-04"}) == "operational_hazard"


def test_misguide_none_when_no_candidate_events():
    assert pick_misguide_candidate({"tax_cut": "2026-01", "typhoon": "2025-07"}) is None


def test_misguide_none_on_all_none():
    events = dict(tax_cut=None, tax_raise=None, food_vat_cut=None, typhoon=None,
                  competitor=None, operational_hazard=None, war=None)
    assert pick_misguide_candidate(events) is None


def test_round_money_owner_plausible():
    assert _round_money(1_234_567) == "about 1,235,000 euros"
    assert _round_money(-1_234_567) == "about 1,235,000 euros"
    assert _round_money(1_840) == "about 1,800 euros"
    assert _round_money(120) == "about 120 euros"


def test_round_money_preserves_small_percentage_differences():
    # a real ~12% rent step (typically a few hundred euros) must not
    # collapse to the same displayed figure on both sides -- regression
    # guard for exactly that bug, reported from a generated brief that
    # said "went up 12 percent, from about 700 euros to about 700 euros"
    before, after = _round_money(660), _round_money(739)
    assert before != after
    assert before == "about 660 euros"
    assert after == "about 740 euros"


def test_round_pct():
    assert _round_pct(0.12) == "12 percent"
    assert _round_pct(-0.041) == "-4 percent"


def test_cap_first_does_not_lowercase_rest():
    # str.capitalize() would turn "...stock I lost" into "...stock i lost" —
    # _cap_first must not.
    s = "an overnight failure that cost me, on top of the stock I lost"
    assert _cap_first(s) == "An overnight failure that cost me, on top of the stock I lost"


def test_cap_first_empty_string():
    assert _cap_first("") == ""


def _fake_tables(write_offs, procurement):
    from grocery_sim.simulation import SimulationData
    return SimulationData({"write_offs": write_offs, "procurement": procurement})


def test_shrinkage_rate_values_writeoffs_at_last_paid_cost():
    procurement = pd.DataFrame({
        "uid": [1, 1, 2],
        "unit_cost": [2.0, 2.0, 5.0],
        "delivery_date": ["2025-01-01", "2025-06-01", "2025-01-01"],
    })
    write_offs = pd.DataFrame({"uid": [1, 2], "units": [10, 2]})
    # uid 1 valued at its LAST paid cost (2.0, unchanged here) x 10 units
    # = 20; uid 2 at 5.0 x 2 = 10; total write-off value 30 / revenue 300
    assert _shrinkage_rate(_fake_tables(write_offs, procurement), 300.0) == 30.0 / 300.0


def test_shrinkage_rate_zero_writeoffs():
    procurement = pd.DataFrame({"uid": [1], "unit_cost": [2.0], "delivery_date": ["2025-01-01"]})
    write_offs = pd.DataFrame({"uid": [], "units": []})
    assert _shrinkage_rate(_fake_tables(write_offs, procurement), 100.0) == 0.0


def test_shrinkage_rate_none_without_revenue():
    procurement = pd.DataFrame({"uid": [1], "unit_cost": [2.0], "delivery_date": ["2025-01-01"]})
    write_offs = pd.DataFrame({"uid": [1], "units": [1]})
    assert _shrinkage_rate(_fake_tables(write_offs, procurement), 0.0) is None


def test_task_type_optimize_when_struggling_with_elevated_shrinkage():
    assert _task_type("struggling", 1, 0.12, None) == "optimize"
    assert _task_type("uncertain", 3, 0.09, 0.0) == "optimize"


def test_task_type_diagnose_when_shrinkage_within_calibrated_band():
    # empirically (see describe.py's _task_type docstring), ordinary
    # shrinkage sits around 4-6% regardless of outcome -- not an
    # operational problem to flag on its own
    assert _task_type("struggling", 1, 0.05, None) == "diagnose"


def test_task_type_invest_when_thriving_with_real_retained_earnings():
    floor = PHASE5["finance"]["infra_capex"]
    assert _task_type("thriving", 3, None, floor) == "invest"
    assert _task_type("thriving", 3, None, floor * 10) == "invest"


def test_task_type_no_invest_below_floor_or_off_three_year_horizon():
    floor = PHASE5["finance"]["infra_capex"]
    # thriving but retained earnings below the smallest investment's own
    # capex -- not a plausible capital-allocation ask yet
    assert _task_type("thriving", 3, None, floor - 1) == "diagnose"
    # the retained-earnings mechanism only exists on the three-year horizon
    assert _task_type("thriving", 1, None, floor * 10) == "diagnose"
    # thriving with no retained-earnings signal at all (one-year run)
    assert _task_type("thriving", 1, None, None) == "diagnose"


def test_task_type_thriving_ignores_shrinkage():
    # a thriving shop's shrinkage never triggers "optimize" -- that framing
    # is reserved for shops that are not already doing well
    assert _task_type("thriving", 1, 0.20, None) == "diagnose"
