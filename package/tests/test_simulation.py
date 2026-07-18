"""Integration tests: real simulations across a spread of settings. Uses
the session-scoped fixtures in conftest.py for the expensive baseline/
stress cases, and runs a handful of extra one-off sims for the settings
those fixtures don't cover (individual events, individual investments,
reproducibility, a seed sweep).
"""

from __future__ import annotations

import pytest

from .conftest import make_settings, run


def test_baseline_1yr_structural_ok(baseline_1yr):
    assert baseline_1yr.validation["structural_ok"] is True


def test_baseline_3yr_structural_ok(baseline_3yr):
    assert baseline_3yr.validation["structural_ok"] is True


def test_stress_combo_structural_ok(stress_combo):
    assert stress_combo.validation["structural_ok"] is True


def test_baseline_tables_present(baseline_1yr):
    tables = baseline_1yr.data()
    for name in ("receipts", "cost_sheet", "tax_statement", "price_history",
                 "procurement", "write_offs", "weather", "calendar"):
        assert name in tables.keys()
        assert len(tables[name]) > 0


@pytest.mark.parametrize("event_name,date", [
    ("war", "2025-03-01"),
    ("typhoon", "2025-07-15"),
    ("food_vat_cut", "2025-05-01"),
    ("tax_cut", "2025-06-01"),
    ("tax_raise", "2025-07-01"),
])
def test_single_event_1yr_structural_ok(event_name, date):
    sim = run(make_settings(basic=dict(year=1, random_seed=200), events={event_name: date}))
    try:
        assert sim.validation["structural_ok"] is True
    finally:
        sim.cleanup()


@pytest.mark.parametrize("event_name,date", [
    ("competitor", "2026-06-01"),
    ("operational_hazard", "2027-04-01"),
])
def test_single_event_3yr_only_structural_ok(event_name, date):
    sim = run(make_settings(basic=dict(year=3, random_seed=201), events={event_name: date}))
    try:
        assert sim.validation["structural_ok"] is True
    finally:
        sim.cleanup()


@pytest.mark.parametrize("investment", ["more_staff", "bigger_store", "upgrade_infrastructure"])
def test_single_investment_3yr_structural_ok(investment):
    inv = dict(more_staff=False, bigger_store=False, upgrade_infrastructure=False)
    inv[investment] = True
    sim = run(make_settings(
        basic=dict(year=3, random_seed=202, retain_earning=True, retain_earning_from="2026-01"),
        potential_investment=inv,
    ))
    try:
        assert sim.validation["structural_ok"] is True
    finally:
        sim.cleanup()


def test_reproducibility_same_seed_same_revenue():
    settings = make_settings(basic=dict(year=1, random_seed=303))
    sim1 = run(settings)
    sim2 = run(settings)
    try:
        rev1 = float(sim1.data().cost_sheet["revenue"].sum())
        rev2 = float(sim2.data().cost_sheet["revenue"].sum())
        assert rev1 == rev2
    finally:
        sim1.cleanup()
        sim2.cleanup()


def test_different_seeds_give_different_revenue():
    sim1 = run(make_settings(basic=dict(year=1, random_seed=1)))
    sim2 = run(make_settings(basic=dict(year=1, random_seed=2)))
    try:
        rev1 = float(sim1.data().cost_sheet["revenue"].sum())
        rev2 = float(sim2.data().cost_sheet["revenue"].sum())
        assert rev1 != rev2
    finally:
        sim1.cleanup()
        sim2.cleanup()


@pytest.mark.parametrize("seed", [11, 22, 33])
def test_seed_sweep_3yr_structural_ok(seed):
    sim = run(make_settings(basic=dict(year=3, random_seed=seed)))
    try:
        assert sim.validation["structural_ok"] is True
    finally:
        sim.cleanup()


def test_tax_statement_arithmetic_consistent(stress_combo):
    """The exported tax_statement.csv, read fresh off disk (not internal
    simulator state), should still satisfy after == before - tax per year."""
    tx = stress_combo.data().tax_statement
    for _, row in tx.iterrows():
        assert row["profit_after_tax"] == pytest.approx(
            row["profit_before_tax"] - row["profit_tax"], abs=1e-6
        )
