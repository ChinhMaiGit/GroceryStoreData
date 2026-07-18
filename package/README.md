# grocery-sim

A standalone, installable Python package that simulates three years in the
life of a small neighborhood grocery store — customers, an owner, a
calendar of weather and macro shocks, a daily market, and a full paper
trail (receipts, invoices, a ledger, a tax filing) — and hands the result
back as an object with a small, fixed API.

Every number it produces has a documented, traceable cause; nothing is
sampled from a convenient distribution and called a business. **The theory
behind why the model is built this way — the distributional choices, the
causal structure, the exogenous/endogenous split — is not repeated here.**
See `paper/paper.pdf` (and `documents/PHASE1..5_DETAILS.md` for the
underlying design documents) in the parent project for that. This README
only covers the package: how to run it, what you can configure, and what
each method returns.

## Install

From this directory:

```bash
uv pip install -e .
# or: pip install -e .
```

## How it works

A run has four stages, always in this order:

1. **`setup(settings)`** validates a settings dict against a fixed schema
   (below) and resolves it against defaults. Nothing is simulated yet —
   this step only catches typos, impossible dates, and unsupported
   combinations early, raising `SettingsError`.
2. **`simulate()`** builds the world (locations, customers, the owner's
   opening decision), performs the scripted year(s) day by day, runs the
   recording layer (which deliberately dirties the visible documents the
   way real paperwork is dirty), and exports the result. It then
   automatically runs the validation battery (below) and raises
   `ValidationError` if a bookkeeping invariant broke.
3. **Query the result** — `data()`, `db()`, `erd()`, `describe()` — as many
   times as you like, in any order, without re-running anything.
4. **`create_analysis(path)`** scaffolds a marimo notebook against the
   result, and `export_settings(path)` / `cleanup()` handle reuse and
   teardown.

Internally, every run is built from two layers that never talk to each
other in the reverse direction:

- **A scripted, exogenous layer** — the calendar, weather, and the macro
  events described below — decided in advance, independent of anything the
  simulated customers or owner do. This is what `settings.events` controls.
- **An emergent, endogenous layer** — individual customers making a
  discrete choice at the shelf, an owner following fixed heuristic rules
  (restocking, pricing, and — if allowed — expanding) in response to what
  he actually observes, never to the ground truth. This is what
  `settings.potential_investment` partially controls (see below): you can
  allow or forbid a decision, but you cannot script when or whether it
  actually happens — that stays the model's own emergent output.

The practical consequence: two runs that differ only in one scripted event
being present or absent are otherwise identical (the same customers make
the same choices on the same days), so the difference between them is an
exact causal effect, not a correlation. This is also why nothing in the
package lets one event *cause* another — a "war causes a government
response two months later" story has to be authored by you as two
separately dated events; the model has no mechanism for one event to
trigger another, on purpose, because real macro causation is exogenous
from a single shop's point of view too.

## The object API

```python
from grocery_sim import GroceryStoreSimulation, ValidationError

sim = GroceryStoreSimulation()
```

| Method / attribute | Returns |
|---|---|
| `sim.setup(settings)` | `self`, after validating; raises `SettingsError` |
| `sim.simulate(out_dir=None)` | `self`, after running phases 1-3 + recording + export + validation; raises `ValidationError` on a structural failure |
| `sim.data(include_hidden=False)` | a `SimulationData` object — attribute access per table (`sim.data().receipts`, `.cost_sheet`, ...) plus a compact schema summary as its `repr()` |
| `sim.db(path=None, include_hidden=False)` | a `duckdb` connection with every table loaded (`path=None` → in-memory) |
| `sim.erd(include_hidden=False)` | a Mermaid `erDiagram` string, inferred from shared key-like column names across the exported tables |
| `sim.describe()` | a business-case brief (markdown string): a letter, a Q&A-style intake interview (year-by-year narrative, honest records caveats), a data table, and a question list, all narrated by a reproducible fictional owner persona (name, gender/pronoun, age, prior career — keyed off `random_seed`) around this run's own real events and results. Costs one extra internal simulation on the first call if a competitor/war/operational_hazard event is active (a counterfactual twin, used to ground the owner's guess about the cause); cached after that, so repeated calls are free and return the same text |
| `sim.settings` | the resolved settings dict (JSON round-trippable) |
| `sim.validation` | the full validation report: `{"structural_ok": bool, "checks": [...]}` |
| `sim.create_analysis(path, mode="student")` | writes a scaffolded marimo notebook to `path`; `mode="instructor"` also fills in starter queries |
| `sim.export_settings(path)` | writes `sim.settings` to JSON, reloadable via `sim2.setup(json.load(open(path)))` |
| `sim.cleanup()` | removes the temporary export directory, if `simulate()` created one |

`sim.data()` and `sim.db()` both accept `include_hidden=True` to also load
the hidden answer-key tables (customer-level true parameters, the demand
modifiers, the profit triptych, ...) — useful for building or checking an
analysis, never appropriate to hand to a student working the case cold.

## Possible scenarios: the settings schema

```python
settings = dict(
    basic = dict(
        name = "Corner Grocer",
        random_seed = 1124,
        year = 3,                       # 1 or 3 — see "Known limitations"
        budget = 60_000,
        year_start = "2025",
        retain_earning = True,          # Phase 5 only; required for any expansion
        retain_earning_from = "2026-01",
    ),
    events = dict(
        war = None,                      # broad supply shock, all categories
        typhoon = None,                  # 3-day storm: traffic collapse + fresh-goods cost spike
        food_vat_cut = None,              # reduced VAT-rate group cut to 5%
        tax_cut = None,                   # standard VAT-rate group cut to 15%
        tax_raise = None,                 # a direct levy on gross revenue
        competitor = None,                # discounter entry; requires year == 3, single-date only
        operational_hazard = None,        # freezer/equipment failure; requires year == 3
    ),
    potential_investment = dict(
        more_staff = True,               # allows the hire-and-expand decision to fire
        bigger_store = False,            # allows a shelf-capacity expansion to fire
        upgrade_infrastructure = False,  # allows a spoilage-reducing upgrade to fire
    ),
)
```

**`war`, `typhoon`, `food_vat_cut`, `tax_cut`, `tax_raise`, and
`operational_hazard`** each also accept a *list* of dates instead of one,
to make the same event happen more than once:

```python
events = dict(war = ["2025-02", "2026-06", "2027-11"])
```

**`competitor` stays single-date.** It is a permanent regime change once
triggered (a defection ramp that never resets, not a transient shock), so a
second entry would need its own calibration decision about how two
competitors' effects compound — not modeled; passing a list raises.

**`potential_investment` is an allow/forbid switch only.** All three keys
share one rule: you can never set a threshold, a date, or a size for any of
them. Each fires — or doesn't — entirely on the model's own retained-
earnings/spendable-cash trigger, independently of the others, and any
combination of the three can fire in the same three-year run. `more_store`
(a second physical location) is not in the schema at all — passing it,
even as `False`, raises `SettingsError`.

For a worked example that pushes nearly every one of these at once — three
wars, three typhoons, three equipment failures, both tax cuts, a competitor
entry, and an endogenous expansion, all in one three-year run — see
`cases/extreme_stress_test/analysis_notebook.py`.

## Validation

Every `simulate()` call runs the full validation battery automatically and
prints a three-part report. Checks are tiered:

- **structural** — bookkeeping identities, conservation, referential
  integrity, the recording layer's recoverability contract. These have
  nothing to do with which events are scripted; a failure here is a
  generator bug, always. `simulate()` raises `ValidationError` if any
  structural check fails.
- **core** — exactly one check, `oracle > realized (information pays)`: is
  a perfectly-informed operator's profit actually higher than the
  realistically-forecasting owner's? Reported prominently, never fatal — a
  dense enough pile-up of shocks can legitimately erase this gap (the
  extreme-stress-test case is a worked example where it does).
- **band** — magnitude ranges calibrated against a quiet, one-year
  baseline (Fri-Sun revenue split, card share, spoilage as a percent of
  revenue, repricing cadence, ...). These are *expected* to diverge once
  real events are scripted, or occasionally even in a quiet run from
  ordinary seed variance. Reported, never fatal.

Access the summary directly: `sim.validation["structural_ok"]` and
`[c for c in sim.validation["checks"] if c["tier"] == "core"]`.

Two bands ("realized capture near 0.65 target" and "repricing cadence
realistic") were found running consistently out of range on multi-year
runs during development; one turned out to be a real denominator bug in
the validator (now fixed), the other was genuine seed variance on an
already-tight calibration (left as-is). See the inline comments beside
each check in `validate.py` for the full account if you need to trust a
specific check's history.

## Testing

```bash
uv pip install -e ".[test]"
pytest
```

`tests/` is a real regression suite, not the ad hoc scripts used during
development: settings-validation errors (`test_settings.py`), `persona.py`
in isolation (`test_persona.py`), `describe.py`'s pure logic
(`test_describe_unit.py`), and full simulations across a spread of
settings — every event individually, every investment individually, all
of them combined, several seeds, reproducibility, and `describe()` against
real results (`test_simulation.py`, `test_describe_integration.py`). The
simulation-backed tests are slow (each one is a real multi-year run); the
suite reuses a handful of session-scoped fixtures rather than re-simulating
per test, but a full run still takes tens of minutes.

## Known limitations (read before relying on these)

- **`basic.year` only supports `1` or `3`.** The three-year arc's holiday
  calendar, panel churn, and scripted year-two/year-three events are
  hand-calibrated to exactly three years; arbitrary horizons are future work.
- **`basic.year_start` relabels exported dates but the internal calendar
  always runs from 2025-01-01.** Day-of-week alignment follows 2025's
  calendar, not the real target year's, if you pick a `year_start` other
  than `"2025"`.
- **`potential_investment.more_store` is excluded entirely** — see above.
- **`events.competitor` is single-fire** — see above.
- **`describe()` and `create_analysis()` are templates, not the full
  authoring apparatus.** `describe()` builds a fictional owner (name,
  gender/pronoun, age, prior career, town — cosmetic only, see
  `persona.py`) and a narrative brief around this run's *real* settings
  and results: a letter, a Q&A-style intake interview with one block per
  year (which events fired, when, what they cost, whether an investment
  paid for itself), and an honest records-imperfections note computed
  directly from the exported tables (void/mis-ring counts, duplicate
  invoice postings, weather-log gaps — never invented, never from the
  hidden answer key). Every number in the brief is rounded the way an
  owner would round it in their own head — never a hidden simulation
  parameter (the case method's epistemic firewall, see `describe.py`'s
  module docstring). If a competitor, war, or operational-hazard event is
  active, the owner fixates on it as the likely cause of a bad year — a
  realistic but not necessarily correct instinct — and `describe()`
  quietly runs one counterfactual twin (same settings and seed, that
  event removed) to decide, honestly, how confident the brief's closing
  "Stakes" section should sound; the computed number itself is never
  printed. This makes the *first* `describe()` call on a run with such an
  event noticeably slower (one extra internal simulation); the result is
  cached on the instance afterwards. `create_analysis()` scaffolds a
  condensed slice of the project's analysis catalog with correct,
  executable starter queries in instructor mode — a running start, not a
  finished analysis.
- **`db()`'s `random_seed` scoping is process-global, not instance-local.**
  Two `GroceryStoreSimulation` instances with different seeds must be run
  sequentially, not concurrently, in the same process.

## Package layout

See `grocery_sim/__init__.py` for the module-by-module map. The package
mirrors the original `datagen/` implementation's one-module-per-design-
document structure (`phase1.py`, `phase2.py`, `phase3.py`, `world.py`,
`recording.py`, `export.py`, `keys.py`, `params.py`), plus this package's
own additions: `events.py` (the composer described above), `settings.py`
(the schema), `schema.py` (the ERD), `persona.py` (the fictional owner
identity), `describe.py` (the brief built around that persona),
`analysis.py`, and `simulation.py` (the `GroceryStoreSimulation` class
itself). `validate.py`
is the original single-arm validation battery, generalized into the tiered
structural/core/band report described above.
