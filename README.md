# GroceryStoreData

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
| `paper/` | The theoretical paper (LaTeX source + compiled PDF) |
| `documents/` | The design documents the paper and package are built from: `PHASE1..5_DETAILS.md`, `ACCOUNTING.md`, `ANALYSIS_CATALOG.md`, `CASE_WRITING_GUIDE.md` |
| `datagen/` | The original, non-packaged reference implementation behind the pre-generated arms and cases below; frozen as a historical reference — `package/grocery_sim/` is the actively developed copy |
| `data/scenarios/` | Pre-generated reference arms (the baseline, CRN-twin policy scenarios, and the three-year arc), each with its `visible/` analyst dataset and `hidden/` answer key |
| `cases/` | Business cases built on specific arms — a client-facing brief, an instructor appendix, and a worked analysis notebook per case |
| `analyses/` | Marimo notebooks working through the analysis catalog on the reference arms |
| `draft/` | The archived original design notebook, superseded by `documents/` and the package |

## Which one do I want?

- **Generate your own data under your own scenario** → `package/`, the
  `grocery_sim` package.
- **Understand why the model is built the way it is** → `paper/paper.pdf`.
- **See a worked, full-depth business-analytics engagement on
  pre-generated data** → `cases/` and `analyses/`, built on the reference
  arms in `data/scenarios/`.
