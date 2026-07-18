# grocery-sim

[![PyPI](https://img.shields.io/pypi/v/grocery-sim.svg)](https://pypi.org/project/grocery-sim/)

A standalone, installable Python package that simulates one or three years
in the life of a small neighborhood grocery store — customers, an owner, a
calendar of weather and macro shocks, a daily market, and a full paper
trail (receipts, invoices, a ledger, a tax filing) — and hands the result
back as an object with a small, fixed API. The one-year horizon is the
default; the three-year arc (customer turnover, retained earnings, an
endogenous expansion decision) is opt-in via `basic.year = 3` — see
"Possible scenarios" below.

Every number it produces has a documented, traceable cause; nothing is
sampled from a convenient distribution and called a business. **The theory
behind why the model is built this way — the distributional choices, the
causal structure, the exogenous/endogenous split — is not repeated here.**
This package is developed inside the
[GroceryStoreData](https://github.com/ChinhMaiGit/GroceryStoreData)
monorepo — see
[`paper/paper.pdf`](https://github.com/ChinhMaiGit/GroceryStoreData/blob/main/paper/paper.pdf)
there for the theoretical paper, and `documents/PHASE1..5_DETAILS.md` for
the underlying design documents. This README only covers the package
itself: how to run it, what you can configure, and what each method
returns.

## Install

```bash
pip install grocery-sim
# or: uv add grocery-sim
```

From a checkout of the monorepo instead (for development):

```bash
cd package
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

One practical consequence of this split: nothing in the package lets one
event *cause* another. A "war causes a government response two months
later" story has to be authored by you as two separately dated events in
`settings.events`.

## The object API

```python
from grocery_sim import GroceryStoreSimulation

sim = GroceryStoreSimulation()
```

| Method / attribute | Returns |
|---|---|
| `sim.setup(settings)` | `self`, after validating; raises `SettingsError` |
| `sim.simulate(out_dir=None)` | `self`, after running phases 1-3 + recording + export + validation; raises `ValidationError` on a structural failure |
| `sim.data(include_hidden=False)` | a `SimulationData` object — attribute access per table (`sim.data().receipts`, `.cost_sheet`, ...) plus a compact schema summary as its `repr()` |
| `sim.db(path=None, include_hidden=False)` | a `duckdb` connection with every table loaded (`path=None` → in-memory) |
| `sim.erd(include_hidden=False)` | a Mermaid `erDiagram` string, inferred from shared key-like column names across the exported tables |
| `sim.describe()` | a business-case brief (markdown string): a persona-narrated letter, intake interview, data table, and question list built from this run's real events and results — see "Known limitations" for what it costs and doesn't do |
| `sim.settings` | the resolved settings dict (JSON round-trippable) |
| `sim.validation` | the full validation report: `{"structural_ok": bool, "checks": [...]}` |
| `sim.create_analysis(path, mode="student")` | writes a scaffolded marimo notebook to `path`; `mode="instructor"` also fills in starter queries |
| `sim.export_settings(path)` | writes `sim.settings` to JSON, reloadable via `sim2.setup(json.load(open(path)))` |
| `sim.cleanup()` | removes the temporary export directory, if `simulate()` created one |

`sim.data()` and `sim.db()` both accept `include_hidden=True` to also load
the hidden answer-key tables (customer-level true parameters, the demand
modifiers, the profit triptych, ...) — useful for building or checking an
analysis, never appropriate to hand to a student working the case cold.

`simulate()` raises `ValidationError` (importable from `grocery_sim`)
only when a structural invariant breaks — a generator bug, never an
expected consequence of your settings — so it is safe to leave uncaught
in ordinary use; catch it only if you want to handle that failure
mode explicitly:

```python
from grocery_sim import GroceryStoreSimulation, ValidationError

sim = GroceryStoreSimulation()
try:
    sim.setup(settings).simulate()
except ValidationError as exc:
    print(f"generator bug, please report: {exc}")
```

**Working with `sim.data()`** — a `SimulationData` object, one pandas
`DataFrame` per table, addressable either as an attribute or by name:

```python
data = sim.data()
print(data)                        # repr(): every table, its row count, its columns
data.receipts.head()               # receipt_id, hour, payment, customer_id,
                                    # uid, qty, unit_price, promo, ref_receipt_id, date
data.cost_sheet[["month", "revenue", "procurement", "rent", "wages"]]
data["cost_sheet"]                 # same table, looked up by name instead of attribute
list(data.keys())                  # every table name actually exported this run
```

**Working with `sim.db()`** — a live `duckdb` connection with every table
already loaded, for anyone who'd rather write SQL than pandas:

```python
con = sim.db()
con.sql("""
    SELECT date, SUM(qty * unit_price) AS revenue
    FROM receipts
    GROUP BY date
    ORDER BY date
""").df()                          # -> a pandas DataFrame, one row per day
```

**Working with `sim.erd()`** — a plain Mermaid `erDiagram` string, not an
image; `print()` it for readable text, or render it anywhere that
understands Mermaid syntax:

```python
print(sim.erd())                   # readable as-is in a terminal

# in a marimo notebook, this renders as an actual diagram:
import marimo as mo
mo.mermaid(sim.erd())

# or paste the printed text into https://mermaid.live, a GitHub
# markdown code fence tagged ```mermaid, or VS Code's Mermaid preview
```

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
[`cases/extreme_stress_test/analysis_notebook.py`](https://github.com/ChinhMaiGit/GroceryStoreData/blob/main/cases/extreme_stress_test/analysis_notebook.py)
in the monorepo (not shipped inside this package's own distribution).

## What kind of analysis does this support?

`documents/ANALYSIS_CATALOG.md` in the monorepo lists concrete, gradeable
questions across eight layers — cleaning, description, causal diagnosis,
prediction, prescription, a policy lab (CRN-twin counterfactuals), and,
on the three-year arc, trend/churn/capital analysis. Its own suggested
methods lean econometric: conditional logit, hierarchical Bayesian
demand models, STL trend-seasonality decomposition, survival analysis
for churn, marketing-mix decomposition.

Standard ML — gradient boosting, bagging, clustering — fits just as
well even though the catalog doesn't frame it that way: stockout-risk
prediction and (on the three-year arc) customer churn are ordinary
classification problems; customer segmentation via clustering is a
natural fit for the behavioral features in `receipts`. What makes any
of this more than a generic tabular exercise is that the generating
mechanism is fully known: a model can be graded not just on held-out
accuracy but on whether it recovered the *true* structure (do a
classifier's feature importances match the real generative drivers? do
clusters actually separate on the same lines as the hidden true price
sensitivity or persistence type?) — a check no real dataset can offer.

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

## Testing (from a monorepo checkout)

```bash
cd package
uv pip install -e ".[test]"
pytest
```

Not needed to use the package — only relevant if you're modifying
`grocery_sim` itself. `tests/` covers settings validation, `persona.py`
and `describe.py` in isolation, and full simulations across a spread of
settings; the simulation-backed tests are slow (each is a real run), so
a full pass takes tens of minutes. CI runs this suite on every push and
pull request against `main`.

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

For the module-by-module internals (only relevant if you're extending
the package rather than using it), see `grocery_sim/__init__.py`'s own
docstring.
