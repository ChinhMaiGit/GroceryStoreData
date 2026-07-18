"""Shared settings builder and expensive-fixture cache for the regression
suite. Expensive fixtures (real 1-year or 3-year simulations) are
session-scoped and reused across many assertions on purpose — each one
costs real wall-clock time, so the suite is organized to run the minimum
number of simulations needed to cover the settings surface.
"""

from __future__ import annotations

import pytest

from grocery_sim import GroceryStoreSimulation


def make_settings(**overrides) -> dict:
    """A full, valid settings dict, deep enough to pass resolve() as-is.
    Pass e.g. basic=dict(year=3), events=dict(war="2025-03") to override
    just those leaf keys — sections not mentioned keep their defaults."""
    s = {
        "basic": dict(
            name="Test Shop",
            random_seed=1,
            year=1,
            budget=60_000,
            year_start="2025",
            retain_earning=False,
            retain_earning_from=None,
        ),
        "events": dict(
            tax_cut=None,
            tax_raise=None,
            food_vat_cut=None,
            typhoon=None,
            competitor=None,
            operational_hazard=None,
            war=None,
        ),
        "potential_investment": dict(
            more_staff=True,
            bigger_store=False,
            upgrade_infrastructure=False,
        ),
    }
    for section, kv in overrides.items():
        s[section].update(kv)
    return s


def run(settings: dict) -> GroceryStoreSimulation:
    sim = GroceryStoreSimulation()
    sim.setup(settings).simulate()
    return sim


@pytest.fixture(scope="session")
def baseline_1yr():
    sim = run(make_settings(basic=dict(year=1, random_seed=101)))
    yield sim
    sim.cleanup()


@pytest.fixture(scope="session")
def baseline_3yr():
    sim = run(make_settings(basic=dict(year=3, random_seed=102)))
    yield sim
    sim.cleanup()


@pytest.fixture(scope="session")
def stress_combo():
    """Every event type at once, all three investments allowed — the same
    shape as cases/extreme_stress_test and cases/story_quality_check, so a
    regression there is likely to show up here too."""
    settings = make_settings(
        basic=dict(
            year=3, random_seed=103,
            retain_earning=True, retain_earning_from="2026-01",
        ),
        events=dict(
            war=["2025-03-01", "2026-09-01"],
            typhoon="2025-07-15",
            food_vat_cut="2025-05-01",
            tax_cut="2026-02-01",
            tax_raise="2027-01-01",
            competitor="2026-06-01",
            operational_hazard="2027-04-01",
        ),
        potential_investment=dict(
            more_staff=True, bigger_store=True, upgrade_infrastructure=True,
        ),
    )
    sim = run(settings)
    yield sim
    sim.cleanup()
