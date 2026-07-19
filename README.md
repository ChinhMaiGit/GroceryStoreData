# GroceryStoreData

[![tests](https://github.com/ChinhMaiGit/GroceryStoreData/actions/workflows/tests.yml/badge.svg)](https://github.com/ChinhMaiGit/GroceryStoreData/actions/workflows/tests.yml)

A structural microsimulation of a small neighborhood grocery store —
customers, an owner, a calendar of weather and macro shocks, a daily
market, and a full paper trail (receipts, invoices, a ledger, a tax
filing) — with a fully known, documented causal ground truth. Every
number in the output has a traceable cause; nothing is sampled from a
convenient distribution and called a business.

The simulator ships as **`grocery_sim`**, a standalone, installable
Python package with a small object API:

```python
from grocery_sim import GroceryStoreSimulation

sim = GroceryStoreSimulation()
sim.setup(settings)   # a scripted macro calendar + endogenous investment toggles
sim.simulate()         # builds the world, performs the year(s), validates the result
sim.data()             # receipts, invoices, the ledger, the tax filing, ...
```

**→ [`package/README.md`](package/README.md)** is the package's own
documentation: installation, the full object API, the settings schema
(every scriptable event and endogenous investment), and the validation
battery run automatically on every `simulate()` call.

**→ [`paper/paper.pdf`](paper/paper.pdf)** is the theoretical paper: why
the model is built the way it is, every distributional choice defended,
the causal structure behind the scripted/emergent split, and a literature
review positioning it against other approaches to synthetic business data.

## Install

```bash
cd package
uv pip install -e .
```

## Repository layout

| Path | Contents |
| --- | --- |
| `package/` | The `grocery_sim` package — install and use this |
| `paper/` | The theoretical paper (LaTeX source + compiled PDF), plus a draft JOSE-style software paper |
| `documents/` | The design documents the paper and package are built from: `PHASE1..5_DETAILS.md`, `ACCOUNTING.md`, `ANALYSIS_CATALOG.md`, `CASE_WRITING_GUIDE.md` |
| `data/scenarios/` | Pre-generated reference arms (the baseline, CRN-twin policy scenarios, and the three-year arc), each with its `visible/` analyst dataset and `hidden/` answer key |
| `cases/` | Business cases built on specific arms — a client-facing brief, an instructor appendix, and a worked analysis notebook per case |
| `archive/` | Pre-package exploratory material, kept working but no longer developed: `datagen/` (the original, non-packaged reference implementation behind `data/scenarios/` — `package/grocery_sim/` is the actively developed copy), `generate_dataset.py` (its CLI entry point), `analyses/` (marimo notebooks working through the analysis catalog on the reference arms), and `draft/` (the original design notebook) |

## What kind of analysis does this support?

`documents/ANALYSIS_CATALOG.md` lists concrete, gradeable questions —
every one answerable from an arm's `visible/` data and checkable against
its `hidden/` answer key — across eight layers, in the order a real
engagement would tackle them:

| Layer | What it asks |
| --- | --- |
| 0 — Clean | Reconcile duplicate receipts/invoices, mistyped counts, and other recording-layer defects before trusting anything |
| 1 — Describe | Where the money goes, when people shop, what a basket looks like |
| 2 — Diagnose causes | Does weather actually move revenue once the calendar is controlled for; how fast does a cost shock reach the shelf |
| 3 — Predict | Demand forecasting against a seasonal-naive baseline, stockout risk, early-warning on at-risk customers |
| 4 — Prescribe | Redesign the ordering policy, repricing, hire/expand decisions — priced against the believed/realized/oracle profit triptych |
| 5 — Policy lab | CRN-twin scenario arms make every counterfactual exact: what a tax cut actually did, what a competitor actually cost |
| 6 — Advanced/structural | Discrete-choice estimation, hierarchical Bayesian demand models, marketing-mix decomposition, DAG-consistency checks |
| 7 — The three-year arc | Trend vs. season, churn, structural breaks, capital decisions (`3y_baseline` and its twins only) |

Its own suggested methods lean econometric — conditional logit,
hierarchical Bayesian demand models, STL trend-seasonality
decomposition, survival analysis for churn, marketing-mix decomposition
— but standard ML fits just as naturally even though the catalog
doesn't frame it that way: gradient boosting or bagging for
stockout-risk and (on the three-year arc) churn classification;
clustering for customer segmentation off basket and behavioral
features. What makes any of this more than a generic tabular exercise
is that the generating mechanism is fully known — a model can be
graded not just on held-out accuracy but on whether it recovered the
*true* structure, a check no real dataset can offer.

## Which one do I want?

- **Generate your own data under your own scenario** → `package/`, the
  `grocery_sim` package.
- **Understand why the model is built the way it is** → `paper/paper.pdf`.
- **See a worked, full-depth business-analytics engagement on
  pre-generated data** → `cases/`, built on the reference arms in
  `data/scenarios/`.
