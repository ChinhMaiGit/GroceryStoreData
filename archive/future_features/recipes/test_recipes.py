"""recipes.py's named settings actually produce the task_type they claim
-- run for real, not asserted from the settings shape alone, since
task_type depends on the realized simulated year (see describe.py's
_task_type docstring)."""

from __future__ import annotations

import pytest

from grocery_sim import GroceryStoreSimulation
from grocery_sim.describe import _financial_situation, _shrinkage_rate, _task_type
from grocery_sim.recipes import RECIPES, get_recipe, list_recipes


def _real_task_type(sim: GroceryStoreSimulation) -> str:
    tables = sim.data()
    cs, tx = tables.cost_sheet, tables.tax_statement
    total_revenue = float(cs["revenue"].sum())
    situation = _financial_situation(tx)
    shrinkage = _shrinkage_rate(tables, total_revenue)
    re_final = (
        float(cs["retained_earnings"].iloc[-1])
        if "retained_earnings" in cs.columns and len(cs) else None
    )
    years = sim.settings["basic"]["year"]
    return _task_type(situation, years, shrinkage, re_final)


def test_list_recipes_matches_dict_keys():
    assert list_recipes() == sorted(RECIPES)


def test_get_recipe_unknown_name_raises():
    with pytest.raises(KeyError):
        get_recipe("not_a_real_recipe")


def test_get_recipe_returns_a_mutable_copy():
    a = get_recipe("optimize")
    a["basic"]["random_seed"] = 999
    b = get_recipe("optimize")
    assert b["basic"]["random_seed"] != 999


@pytest.mark.parametrize("name,expected_task_type", [
    ("diagnose_with_candidate", "diagnose"),
    ("diagnose_no_candidate", "diagnose"),
    ("optimize", "optimize"),
    ("invest", "invest"),
])
def test_recipe_produces_claimed_task_type(name, expected_task_type):
    sim = GroceryStoreSimulation()
    sim.setup(get_recipe(name))
    sim.simulate()
    assert _real_task_type(sim) == expected_task_type
    # describe() must actually run clean on every recipe, not just the
    # classification -- a real regression guard for the letter/interview
    # generation this feeds into
    text = sim.describe()
    assert "## The letter" in text
    sim.cleanup()


def test_diagnose_with_candidate_recipe_has_a_grounded_candidate():
    sim = GroceryStoreSimulation()
    sim.setup(get_recipe("diagnose_with_candidate"))
    sim.simulate()
    sim.describe()
    assert sim._misguide["candidate"] == "war"
    sim.cleanup()
