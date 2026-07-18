"""The event composer — turns settings.events / settings.potential_investment
into the declarative `scenario` dict that World(scenario=...) already knows
how to consume (see scenarios.py for the original single-arm registry this
generalizes from).

Design note (read before extending): World's internal calendar always runs
from the fixed epoch PHASE2["start"] = 2025-01-01 (P5's holiday tables are
hand-calibrated to 2025-2027 specifically). A simulation's requested
`year_start` therefore does NOT shift the internal calendar — it only
relabels the exported dates at the end (see simulation.py's `_relabel_dates`).
Every event date the user supplies is first converted to an *offset in days
from the story's own year_start*, and that offset is then applied to the
fixed internal epoch. This keeps every hand-calibrated day-of-year constant
(holidays, the apartment block, the freezer failure, the competitor's entry)
correct in relative terms without touching phase2.py/phase3.py/world.py.

Two events (`competitor`, `operational_hazard`) only exist inside the Phase 5
finance/panel code path (they read `w.p5[...]`, which is None unless the
simulation runs on the three-year horizon), so both require
settings.basic.year == 3. This is enforced in settings.py's validation, not
here.

`war`, `typhoon`, `food_vat_cut`, `tax_cut`, and `tax_raise` additionally
accept a *list* of date labels instead of one, e.g.
`events.war = ["2025-02", "2026-06"]`. This is safe because World already
consumes events_add/weather_edit/vat_schedule/revenue_tax_schedule as lists
— repeating one of these five just appends another entry, with no change to
phase2.py/phase3.py/world.py. `competitor` and `operational_hazard` stay
single-date: they override a single Phase 5 sub-dict's own "t" field, which
is read once, not iterated — see settings.py's `_MULTI_OK_EVENTS` /
`_PHASE5_ONLY_EVENTS`.

`potential_investment.bigger_store` and `.upgrade_infrastructure` follow the
exact same emergent-decision pattern as the pre-existing `.more_staff`: the
user only ever gets an on/off switch (whether the investment is *allowed*),
never a threshold, a date, or a size — when it fires, if it fires, is
entirely the model's own decision, driven by the same retained-earnings/
spendable-cash trigger phase3.py already uses for the hire expansion (see
params.py's PHASE5["finance"] for each investment's own calibrated
threshold/capex). `potential_investment.more_store` (a second physical
location) is excluded entirely — not recognized by the settings schema at
all, since it would need a second Phase One opening MILP solved mid-run.
"""

from __future__ import annotations

import copy
import datetime as dt

from .params import PHASE2, PHASE4, PHASE5

EPOCH = PHASE2["start"]                    # 2025-01-01 — the fixed internal epoch
REDUCED_CATS = "reduced"


def _as_list(value) -> list:
    """None -> []; a bare 'YYYY-MM' string -> [string]; a list -> itself.
    war/typhoon/food_vat_cut/tax_cut all accept either form (settings.py
    has already validated it); competitor/operational_hazard stay
    single-value and are read directly, not through this helper."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _parse_month(label: str) -> dt.date:
    """'2026-09' -> date(2026, 9, 1). A bare year ('2025') -> Jan 1 of that year."""
    parts = label.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    return dt.date(year, month, 1)


def day_offset(
    event_label: str,
    year_start_label: str,
) -> int:
    """The event's 1-indexed day position within the story (day 1 ==
    year_start itself), matching gen_calendar()'s own "t": t=1 is
    PHASE2["start"], t=2 is the day after, etc. — every day-indexed PHASE5
    constant (e.g. the apartment block's t_from=609 for 2026-09-01) is
    calibrated against this same 1-indexed convention, not a 0-indexed one."""
    event_date = _parse_month(event_label)
    start_date = _parse_month(year_start_label)
    return (event_date - start_date).days + 1


def internal_day(
    event_label: str,
    year_start_label: str,
) -> int:
    """The 1-indexed day (`t`) from the fixed internal epoch (2025-01-01)
    that the simulator's own day-indexed arrays expect."""
    return day_offset(event_label, year_start_label)


def month_index(
    label: str,
    year_start_label: str,
) -> int:
    """Convert a 'YYYY-MM' label into the finance ledger's 1-based month
    index (month 1 = the first month of the story), matching
    PHASE5["finance"]["formalize_month"]'s own convention."""
    d, s = _parse_month(label), _parse_month(year_start_label)
    return (d.year - s.year) * 12 + (d.month - s.month) + 1


def compose(
    basic: dict,
    events: dict,
    potential_investment: dict,
) -> dict:
    """Build the `scenario` spec World(scenario=...) consumes, folding every
    active event and investment toggle into one script. Returns {} for an
    all-quiet baseline run (still a legitimate, gradeable arm)."""
    year_start = basic["year_start"]
    n_years = basic["year"]
    scenario: dict = {}
    events_add: list = []
    weather_edit: list = []
    traffic_mult: list = []
    vat_schedule: list = []
    revenue_tax_schedule: list = []
    phase5_overrides: dict = {}

    # --- war: broad supply shock, all categories (P2, one-year-safe) -------
    # Repeatable: each date in the list becomes its own shock event, log-
    # additively stacked on top of whichever other shocks are already live
    # on that day (World's own CostMult assembly, unchanged).
    for label in _as_list(events.get("war")):
        t = internal_day(label, year_start)
        events_add.append({
            "type": "war",
            "start": t,
            "ramp": 14,
            "decay": 120,
            "zeta_all": 0.30,
            "utility_peak": 0.0,
        })

    # --- typhoon: 3-day storm, fresh-goods cost spike -----------------------
    for label in _as_list(events.get("typhoon")):
        t = internal_day(label, year_start)
        weather_edit.append({
            "t_from": t,
            "t_to": t + 2,
            "temp_delta": -5.0,
            "rain_mm": 60.0,
            "wet": 1,
        })
        traffic_mult.append({
            "t_from": t,
            "t_to": t + 2,
            "mult": 0.35,
        })
        events_add.append({
            "type": "typhoon_supply",
            "start": t,
            "ramp": 3,
            "decay": 21,
            "cats": {
                "Fresh Produce": 0.22,
                "Seafood": 0.30,
            },
            "utility_peak": 0.0,
        })

    # --- food_vat_cut: reduced-rate group, halved -------------------------
    # Repeating this with a later date is a legitimate no-op (the rate was
    # already 0.05) unless a scenario also raises it back in between — this
    # is intentionally left to compose, not prevented, since observing the
    # no-op is itself informative.
    for label in _as_list(events.get("food_vat_cut")):
        t = internal_day(label, year_start)
        vat_schedule.append({
            "t_from": t,
            "group": REDUCED_CATS,
            "rate": 0.05,
        })

    # --- tax_cut: standard-rate group cut 20% -> 15% (this project's own
    # reading of a broad, non-food VAT cut; document the choice if you widen
    # it later, e.g. to a profit-tax or payroll-tax cut instead) -----------
    for label in _as_list(events.get("tax_cut")):
        t = internal_day(label, year_start)
        vat_schedule.append({
            "t_from": t,
            "group": "standard",
            "rate": 0.15,
        })

    # --- tax_raise: a direct levy on gross revenue (grocery_sim's own
    # addition — see params.py's PHASE4["revenue_tax_rate"] docstring for
    # why this is a distinct mechanism from tax_cut/food_vat_cut) ----------
    for label in _as_list(events.get("tax_raise")):
        t = internal_day(label, year_start)
        revenue_tax_schedule.append({
            "t_from": t,
            "rate": PHASE4["revenue_tax_rate"],
        })

    # --- competitor / operational_hazard: Phase 5 only, dated by
    # overriding the relevant P5 sub-dict's own "t" (settings.py has already
    # required n_years == 3 before we get here) -----------------------------
    if events.get("competitor"):
        t = internal_day(events["competitor"], year_start)
        _comp = copy.deepcopy(PHASE5["competitor"])
        _comp["t"] = t
        _resp = copy.deepcopy(PHASE5["response"])
        _resp["t"] = t + (PHASE5["response"]["t"] - PHASE5["competitor"]["t"])
        phase5_overrides["competitor"] = _comp
        phase5_overrides["response"] = _resp
    # operational_hazard is repeatable: build one freezer-event dict per
    # date. phase3.py accepts p5["freezer"] as either the original single
    # dict (untouched reference arms) or a list of dicts (this composer's
    # own output whenever the setting is used at all, even for one date, so
    # there is exactly one shape to maintain downstream of this function).
    _hazard_dates = _as_list(events.get("operational_hazard"))
    if _hazard_dates:
        phase5_overrides["freezer"] = [
            {**copy.deepcopy(PHASE5["freezer"]), "t": internal_day(label, year_start)}
            for label in _hazard_dates
        ]

    # --- retained earnings / the three endogenous investments (P5 §4) ------
    # All three share one rule: the user only ever gets an on/off switch.
    # Turning one on does not guarantee it fires, does not set its
    # threshold, date, or size — that stays entirely the model's own
    # emergent decision, exactly like the pre-existing hire expansion.
    # Turning one off permanently disables it (threshold=None), the same
    # mechanism the "3y_no_expansion" CRN twin already uses.
    if n_years == 3:
        finance = dict(PHASE5["finance"])
        if not basic["retain_earning"] or not potential_investment.get("more_staff", True):
            finance["expansion_threshold"] = None
        if not potential_investment.get("bigger_store", False):
            finance["shelf_threshold"] = None
        if not potential_investment.get("upgrade_infrastructure", False):
            finance["infra_threshold"] = None
        if not basic["retain_earning"]:
            finance["retain_ratio"] = 0.0
        if basic["retain_earning_from"] is not None:
            finance["formalize_month"] = month_index(
                basic["retain_earning_from"], year_start,
            )
        if finance != PHASE5["finance"]:
            phase5_overrides["finance"] = finance

    if events_add:
        scenario["events_add"] = events_add
    if weather_edit:
        scenario["weather_edit"] = weather_edit
    if traffic_mult:
        scenario["traffic_mult"] = traffic_mult
    if vat_schedule:
        scenario["vat_schedule"] = vat_schedule
    if revenue_tax_schedule:
        scenario["revenue_tax_schedule"] = revenue_tax_schedule
    if n_years == 3:
        scenario["phase5"] = phase5_overrides
    return scenario
