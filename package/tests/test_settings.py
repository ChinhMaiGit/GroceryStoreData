"""Every SettingsError path in settings.py, checked directly against
setup() — no simulation, so this file runs in well under a second."""

from __future__ import annotations

import pytest

from grocery_sim import GroceryStoreSimulation
from grocery_sim.settings import SettingsError

from .conftest import make_settings


def test_unknown_section_rejected():
    with pytest.raises(SettingsError, match="unknown settings section"):
        GroceryStoreSimulation().setup({"nope": {}})


def test_unknown_leaf_key_rejected():
    with pytest.raises(SettingsError, match="unknown key"):
        GroceryStoreSimulation().setup(make_settings(events=dict(hurricane="2025-01")))


def test_more_store_rejected_even_as_false():
    with pytest.raises(SettingsError, match="unknown key"):
        GroceryStoreSimulation().setup(
            make_settings(potential_investment=dict(more_store=False))
        )


def test_competitor_as_list_rejected():
    with pytest.raises(SettingsError, match="single date, not a list"):
        GroceryStoreSimulation().setup(
            make_settings(
                basic=dict(year=3),
                events=dict(competitor=["2026-01", "2026-06"]),
            )
        )


def test_year_must_be_1_or_3():
    with pytest.raises(SettingsError, match="must be 1 or 3"):
        GroceryStoreSimulation().setup(make_settings(basic=dict(year=2)))


def test_retain_earning_requires_year_3():
    with pytest.raises(SettingsError, match="requires basic.year == 3"):
        GroceryStoreSimulation().setup(
            make_settings(basic=dict(year=1, retain_earning=True))
        )


def test_phase5_only_event_requires_year_3():
    with pytest.raises(SettingsError, match="requires basic.year == 3"):
        GroceryStoreSimulation().setup(
            make_settings(basic=dict(year=1), events=dict(operational_hazard="2025-06"))
        )


def test_event_before_year_start_rejected():
    with pytest.raises(SettingsError, match="before basic.year_start"):
        GroceryStoreSimulation().setup(
            make_settings(basic=dict(year=1, year_start="2025"), events=dict(war="2024-01"))
        )


def test_event_after_horizon_rejected():
    with pytest.raises(SettingsError, match="falls after the story ends"):
        GroceryStoreSimulation().setup(
            make_settings(basic=dict(year=1, year_start="2025"), events=dict(war="2026-01"))
        )


def test_duplicate_date_in_multi_event_rejected():
    with pytest.raises(SettingsError, match="duplicate date"):
        GroceryStoreSimulation().setup(
            make_settings(events=dict(war=["2025-03", "2025-03"]))
        )


def test_empty_event_date_list_rejected():
    with pytest.raises(SettingsError, match="empty list"):
        GroceryStoreSimulation().setup(make_settings(events=dict(war=[])))


def test_negative_budget_rejected():
    with pytest.raises(SettingsError, match="budget must be positive"):
        GroceryStoreSimulation().setup(make_settings(basic=dict(budget=-1)))


def test_empty_name_rejected():
    with pytest.raises(SettingsError, match="non-empty string"):
        GroceryStoreSimulation().setup(make_settings(basic=dict(name="  ")))


def test_valid_settings_pass():
    sim = GroceryStoreSimulation().setup(make_settings())
    assert sim.settings["basic"]["year"] == 1


def test_valid_3yr_settings_with_every_event_pass():
    sim = GroceryStoreSimulation().setup(
        make_settings(
            basic=dict(year=3, retain_earning=True, retain_earning_from="2026-01"),
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
    )
    assert sim.settings["basic"]["year"] == 3


def test_data_before_simulate_raises():
    with pytest.raises(RuntimeError):
        GroceryStoreSimulation().data()


def test_simulate_before_setup_raises():
    with pytest.raises(RuntimeError):
        GroceryStoreSimulation().simulate()
