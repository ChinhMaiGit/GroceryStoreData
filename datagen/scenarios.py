"""Phase 4 — the policy laboratory (documents/PHASE4_DETAILS.md).

A scenario is a declarative set of edits to the exogenous script and the
owner's policy knobs — never to an RNG key — replayed through the identical
keyed market loop, so every difference from the baseline is causally
attributable to the scenario by construction.

Spec fields (all optional):
    events_add    extra Phase-2 cost events (war, typhoon supply shock)
    weather_edit  scripted day ranges: temp delta, rain, wet
    traffic_mult  day-range multipliers on the traffic path
    budget_mult   week-range multipliers on household budgets (income effects)
    vat_schedule  rate-path changes from a given day (P4 §2)
    policy        hired_extra / open_hour / close_hour
    expect        (name, check(world, base) -> bool, detail(world, base) -> str)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from datagen.params import CATS, OUT, PHASE4

REDUCED_CATS = "reduced"      # every category not in vat_standard_categories


def _war_expect(world, base):
    return float(np.max(world.cost_mult["Fresh Produce"])) > 1.25


def _war_detail(world, base):
    return f"peak Fresh Produce cost index {float(np.max(world.cost_mult['Fresh Produce'])):.2f}"


def _typhoon_expect(world, base):
    return float(np.mean(world.lam[250:253])) < 0.5


def _typhoon_detail(world, base):
    return f"storm-day traffic index {float(np.mean(world.lam[250:253])):.2f}"


def _vat_cut_expect(world, base):
    cs = base["cost_sheet"]
    return float(cs.loc[cs.month >= 7, "vat"].sum()) < float(cs.loc[cs.month <= 6, "vat"].sum())


def _vat_cut_detail(world, base):
    cs = base["cost_sheet"]
    return (f"VAT remitted H1 {cs.loc[cs.month <= 6, 'vat'].sum():,.0f} "
            f"-> H2 {cs.loc[cs.month >= 7, 'vat'].sum():,.0f}")


def _rebate_expect(world, base):
    # the honest comparison is CRN-twin April vs the baseline arm's April
    # (April is seasonally weaker than March, so a within-arm month-on-month
    # comparison would hide a genuine income effect)
    cs = base["cost_sheet"]
    _b = pd.read_csv(filepath_or_buffer = OUT / "visible" / "cost_sheet.csv")
    return float(cs.loc[cs.month == 4, "revenue"].iloc[0]) \
        > 1.03 * float(_b.loc[_b.month == 4, "revenue"].iloc[0])


def _rebate_detail(world, base):
    cs = base["cost_sheet"]
    _b = pd.read_csv(filepath_or_buffer = OUT / "visible" / "cost_sheet.csv")
    return (f"April revenue baseline {_b.loc[_b.month == 4, 'revenue'].iloc[0]:,.0f} "
            f"-> rebate arm {cs.loc[cs.month == 4, 'revenue'].iloc[0]:,.0f}")


def _clerk_expect(world, base):
    rec = base["receipts"]
    _extended = ((rec["hour"] < 8) | (rec["hour"] >= 20)) & (rec["qty"] > 0)
    return int(_extended.sum()) > 100 and float(base["cost_sheet"]["wages"].sum()) > 0


def _clerk_detail(world, base):
    rec = base["receipts"]
    _extended = ((rec["hour"] < 8) | (rec["hour"] >= 20)) & (rec["qty"] > 0)
    return (f"{int(_extended.sum())} extended-hours sale lines, "
            f"wages {base['cost_sheet']['wages'].sum():,.0f}")


SCENARIOS = {
    # a broad supply shock erupting June 1: every category's costs surge,
    # tags follow with menu-cost hysteresis, demand adjusts on its own
    "war_june": {
        "description": "war-driven supply shock on all goods from June 1",
        "events_add": [
            {
                "type": "war",
                "start": 152,
                "ramp": 14,
                "decay": 120,
                "zeta_all": 0.30,
                "utility_peak": 0.0,
            },
        ],
        "expect": (
            "all cost paths spike after June",
            _war_expect,
            _war_detail,
        ),
    },
    # a three-day storm, Sep 8-10: footfall collapses, fresh supply chains
    # take a short sharp cost hit, substitution does the rest
    "typhoon_september": {
        "description": "typhoon Sep 8-10: storm weather, traffic collapse, fresh-goods cost spike",
        "weather_edit": [
            {
                "t_from": 251,
                "t_to": 253,
                "temp_delta": -5.0,
                "rain_mm": 60.0,
                "wet": 1,
            },
        ],
        "traffic_mult": [
            {
                "t_from": 251,
                "t_to": 253,
                "mult": 0.35,
            },
        ],
        "events_add": [
            {
                "type": "typhoon_supply",
                "start": 251,
                "ramp": 3,
                "decay": 21,
                "cats": {
                    "Fresh Produce": 0.22,
                    "Seafood": 0.30,
                },
                "utility_peak": 0.0,
            },
        ],
        "expect": (
            "storm days lose most of their footfall",
            _typhoon_expect,
            _typhoon_detail,
        ),
    },
    # a consumer-friendly reform: food VAT halved from July 1 — the analyst's
    # question is how much of it ever reaches the shelf tags
    "food_vat_cut_july": {
        "description": "reduced VAT 10% -> 5% on food from July 1",
        "vat_schedule": [
            {
                "t_from": 182,
                "group": REDUCED_CATS,
                "rate": 0.05,
            },
        ],
        "expect": (
            "H2 VAT remittance falls below H1",
            _vat_cut_expect,
            _vat_cut_detail,
        ),
    },
    # a tax rebate lands in household budgets in weeks 14-17 (April):
    # the income effect, generated where income lives
    "tax_rebate_spring": {
        "description": "household tax rebate: budgets +20% in weeks 14-17",
        "budget_mult": [
            {
                "w_from": 14,
                "w_to": 17,
                "mult": 1.20,
            },
        ],
        "expect": (
            "April revenue jumps on the rebate",
            _rebate_expect,
            _rebate_detail,
        ),
    },
    # hire a clerk and open 7:00-22:00: the extended hours convert part of
    # the 'closed'-cause hidden demand; wages and payroll tax say whether
    # the recovered demand pays for the second person
    "second_clerk": {
        "description": "one hired clerk, opening hours extended to 7:00-22:00",
        "policy": {
            "hired_extra": 1,
            "open_hour": 7,
            "close_hour": 22,
        },
        "expect": (
            "sales appear in the extended hours and wages are paid",
            _clerk_expect,
            _clerk_detail,
        ),
    },
}


def vat_base_rates():
    """Category -> baseline VAT rate, from PHASE4's two-group split."""
    std = set(PHASE4["vat_standard_categories"])
    return {c: (PHASE4["vat_standard"] if c in std else PHASE4["vat_reduced"])
            for c in CATS}
