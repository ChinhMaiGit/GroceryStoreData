"""Named settings recipes, empirically verified to produce a specific
`describe()` task_type -- see describe.py's `_task_type` docstring for
the diagnose/optimize/invest classification this maps to.

These are ordinary settings dicts, exactly the shape
`GroceryStoreSimulation.setup()` already accepts (partial overrides are
deep-merged onto settings.py's DEFAULTS) -- nothing here is a new
mechanism. Each recipe pins a real, verified seed rather than leaving
it to chance: task_type depends on the *realized* simulated year, not
settings alone, so a settings shape that usually lands on a given
task_type can still miss for an arbitrary seed. `tests/test_recipes.py`
runs every recipe for real and checks its task_type on every test run
-- if the simulator's mechanics change enough to break one, that test
will fail rather than silently mis-labeling a generated case, and the
recipe's seed (or its settings) should be re-tuned against a fresh
sweep at that point.

The purpose this exists for: a caller building a library of exercises
(teaching cases, this repo's own cases/) wants deliberate coverage
across the kinds of engagements describe() can produce, not whatever a
random seed happens to land on -- see documents/CASE_WRITING_GUIDE.md
for how a recipe's brief becomes a full case.

Use: `from grocery_sim.recipes import get_recipe; sim.setup(get_recipe("optimize"))`.
"""

from __future__ import annotations

import copy

RECIPES: dict[str, dict] = {
    # thriving, single misguide-eligible event present (a war-driven cost
    # shock) -- the owner has an obvious villain in mind; describe()'s
    # existing candidate/misguide machinery drives the narrative
    "diagnose_with_candidate": {
        "basic": {"year": 1, "random_seed": 210},
        "events": {"war": "2025-03-01"},
    },
    # thriving, three-year horizon, no active events, retained earnings
    # below the invest floor -- no single event to blame, no capital
    # question yet either, just "understand the business properly"
    "diagnose_no_candidate": {
        "basic": {"year": 3, "random_seed": 320},
        "potential_investment": {
            "more_staff": True, "bigger_store": True, "upgrade_infrastructure": True,
        },
    },
    # struggling, elevated shrinkage relative to revenue -- the
    # operational-inefficiency framing rather than a single-cause story
    "optimize": {
        "basic": {"year": 1, "random_seed": 222},
        "events": {"typhoon": "2025-07-15", "food_vat_cut": "2025-05-01"},
    },
    # thriving, three-year horizon, retained earnings comfortably above
    # the smallest investment's own capex -- a capital-allocation
    # question, not a diagnosis
    "invest": {
        "basic": {"year": 3, "random_seed": 300},
    },
}


def get_recipe(name: str) -> dict:
    """A deep copy of a named recipe's settings dict -- safe to mutate
    or pass straight to `GroceryStoreSimulation.setup()`."""
    if name not in RECIPES:
        raise KeyError(f"unknown recipe {name!r}; choose from {sorted(RECIPES)}")
    return copy.deepcopy(RECIPES[name])


def list_recipes() -> list[str]:
    return sorted(RECIPES)
