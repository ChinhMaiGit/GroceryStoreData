"""describe.py's pure logic — no simulation needed."""

from __future__ import annotations

from grocery_sim.describe import _cap_first, _round_money, _round_pct, pick_misguide_candidate


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
