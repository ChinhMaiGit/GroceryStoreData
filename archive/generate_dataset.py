"""Business Data Generator — entry point (archived reference implementation).

Superseded by the `grocery_sim` package (`package/grocery_sim/`), the
actively developed copy — see the top-level README. Kept here, working,
as the historical reference behind the pre-generated arms under
`data/scenarios/`. Run from the repository root as
`uv run python archive/generate_dataset.py ...`.

The implementation lives in the `datagen/` package (now `archive/datagen/`),
one module per design document:

Phase 1  (documents/PHASE1_DETAILS.md -> datagen/phase1.py): the world at
         t=0 — locations, customers, the owner's beliefs, and his opening
         MILP (location, assortment, quantities, staffing, prices).
Phase 2  (documents/PHASE2_DETAILS.md -> datagen/phase2.py): the exogenous
         script of the year — calendar, weather, demand modifiers and tilts,
         traffic, budget paths, macro events, cost and spoilage-factor paths.
Phase 3  (documents/PHASE3_DETAILS.md -> datagen/phase3.py): the daily
         market loop — visits, pantries, softmax choices, stockouts, the
         hidden-demand ledger, guests, refunds, the owner's weekly restock,
         promotions, spoilage, the monthly ledger with the tax layer — plus
         the oracle counterfactual replay. The recording layer (P3 §20 ->
         datagen/recording.py) dirties the visible documents on export.
Phase 4  (documents/PHASE4_DETAILS.md -> datagen/scenarios.py): the policy
         laboratory — CRN-twin scenario arms under edited macro scripts.
Phase 5  (documents/PHASE5_DETAILS.md): the three-year arc — panel churn and
         growth, retained earnings and the endogenous expansion, stepping
         contracts, and the year-two/three shock scripts. Ships as the
         scenario arms prefixed 3y_ (3y_baseline + two CRN twins); their
         year one is byte-identical to the published one-year baseline.

Every arm — the baseline included — lands under data/scenarios/<name>/ with
its own visible/ and hidden/ split. Reproducible end to end from MASTER_SEED.

Run (from the repository root):
      uv run python archive/generate_dataset.py                 (baseline only)
      uv run python archive/generate_dataset.py --scenario war_june
      uv run python archive/generate_dataset.py --scenario 3y_baseline
      uv run python archive/generate_dataset.py --all-scenarios
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from datagen.export import export
from datagen.keys import MASTER_SEED
from datagen.params import OUT
from datagen.phase3 import run_year
from datagen.scenarios import SCENARIOS
from datagen.validate import validate, validate_phase5, validate_scenario
from datagen.world import World


def run_arm(
    scenario = None,
    label = "baseline",
):
    """Build a World (optionally under a scenario spec), perform the year and
    its oracle twin, and return everything an export or comparison needs."""
    t0 = time.time()
    print(f"\n=== arm: {label} ===")
    print("Building the world (Phases 1-2)...")
    world = World(scenario = scenario)
    print("Performing the year (Phase 3)...")
    base = run_year(
        world = world,
        oracle = False,
    )
    print(f"  year done: {len(base['receipts']):,} receipt lines, "
          f"realized profit {base['realized_profit']:,.0f}  [{time.time()-t0:.0f}s]")
    print("Replaying the oracle counterfactual...")
    oracle = run_year(
        world = world,
        oracle = True,
    )
    print(f"  oracle profit {oracle['realized_profit']:,.0f}")
    return world, base, oracle


def summary_row(
    label,
    description,
    base,
    oracle,
):
    cs = base["cost_sheet"]
    return {
        "scenario": label,
        "description": description,
        "revenue": round(float(cs["revenue"].sum()), 2),
        "vat_remitted": round(float(cs["vat"].sum()), 2),
        "payroll_tax": round(float(cs["payroll_tax"].sum()), 2),
        "profit_before_tax": round(base["realized_profit"], 2),
        "profit_tax": round(base["profit_tax"], 2),
        "profit_after_tax": round(base["realized_after_tax"], 2),
        "oracle_profit": round(oracle["realized_profit"], 2),
        "stockout_rate": round(base["stockout_rate"], 4),
        "receipt_lines": len(base["receipts"]),
    }


def main():
    parser = argparse.ArgumentParser(description = "Business Data Generator")
    parser.add_argument(
        "--scenario",
        action = "append",
        default = [],
        choices = sorted(SCENARIOS),
        help = "generate this scenario arm as well (repeatable)",
    )
    parser.add_argument(
        "--all-scenarios",
        action = "store_true",
        help = "generate every reference scenario arm",
    )
    args = parser.parse_args()
    names = sorted(SCENARIOS) if args.all_scenarios else args.scenario

    t0 = time.time()
    rows = []

    # the baseline arm always runs: it defines the reference world every
    # scenario is a CRN twin of, and anchors the comparison file
    world, base, oracle = run_arm(
        scenario = None,
        label = "baseline",
    )
    out_b = OUT / "scenarios" / "baseline"
    dirt = export(
        world = world,
        base = base,
        oracle = oracle,
        out = out_b,
    )
    print(f"Exported to {out_b}")
    validate(
        world = world,
        base = base,
        oracle = oracle,
        dirt = dirt,
    )
    rows.append(summary_row(
        label = "baseline",
        description = "the reference year",
        base = base,
        oracle = oracle,
    ))

    for name in names:
        spec = SCENARIOS[name]
        world_s, base_s, oracle_s = run_arm(
            scenario = spec,
            label = name,
        )
        out_s = OUT / "scenarios" / name
        export(
            world = world_s,
            base = base_s,
            oracle = oracle_s,
            out = out_s,
        )
        print(f"Exported to {out_s}")
        validate_scenario(
            world = world_s,
            base = base_s,
            name = name,
            spec = spec,
        )
        if "phase5" in spec:
            # the three-year arms additionally face the P5 battery: year-one
            # identity, panel accounting, and the RE ledger reconciliation
            validate_phase5(
                world = world_s,
                base = base_s,
                out = out_s,
            )
        rows.append(summary_row(
            label = name,
            description = spec["description"],
            base = base_s,
            oracle = oracle_s,
        ))

    if names:
        _cmp = OUT / "scenarios" / "comparison.csv"
        pd.DataFrame(rows).to_csv(
            path_or_buf = _cmp,
            index = False,
        )
        print(f"\nComparison written to {_cmp}")
    print(f"\nTotal {time.time()-t0:.0f}s, seed {MASTER_SEED}")


if __name__ == "__main__":
    main()
