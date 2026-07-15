# Business Data Generator

A Python simulation of a small neighborhood grocery store, built from microeconomic first principles, that produces a realistic 12-month business dataset with a **known causal ground truth**. The generating mechanisms are fully specified by the author but hidden from the analyst, so the resulting data can honestly demonstrate the complete analytics value chain — from raw transactions to causal inference to optimized decisions.

**Status (July 2026).** The world and its dataset are complete: four settled design phases, a realism-audited generator, a *recording layer* that makes the raw paperwork imperfect the way real paperwork is (duplicates, unlogged waste, typos, refunds) while keeping every defect exactly cleanable against a hidden answer key, a *tax layer* (differential VAT with emergent pass-through, payroll contributions, profit tax), and a *policy laboratory* of CRN-twin scenario arms (war, typhoon, VAT reform, tax rebate, staffing) in which every difference from the baseline is causally attributable by construction. `generate_dataset.py` produces the baseline year in ~35 s with 30 built-in validations; `--all-scenarios` adds the five reference arms and a comparison table. The remaining planned work is the analysis-notebook series (see Roadmap).

**Repository contents**

| File | Purpose |
| --- | --- |
| `draft/Chinh - 20260414 - Data Generation Process.py` | **Archived original draft** of the idea — the Marimo design notebook with the first structural causal model (SCM) and MILP formulation; superseded by `documents/` and `generate_dataset.py`, kept as a historical artifact |
| `SKUs.xlsx` | Hand-crafted product catalog: ~709 SKUs across 12 categories (`uid`, `name`, `brand_level`, `category`, `product_type`, `unit`, `weight_g`, `retail_base_price_EUR`) |
| `documents/PHASE1_DETAILS.md`, `documents/PHASE2_DETAILS.md`, `documents/PHASE3_DETAILS.md`, `documents/PHASE4_DETAILS.md` | The design documents: the world at t=0, the exogenous script of the year, the daily market loop, and the policy laboratory (scenarios + the tax layer) — every distribution defended, every parameter documented |
| `documents/ACCOUNTING.md` | How every euro and every unit moves: revenue recognition, procurement, inventory books, the monthly ledger, the recording layer, and the reconciliation contract |
| `documents/ANALYSIS_CATALOG.md` | The question bank: ~45 gradeable questions across seven layers (cleaning, descriptive, diagnostic, predictive, prescriptive, policy laboratory, structural), each mapped to its method, its visible data, and the answer key that grades it |
| `generate_dataset.py` | Entry point; run `uv run python generate_dataset.py` (~35 s) to regenerate the baseline arm and its 30 validations, byte-reproducible from the master seed; `--scenario <name>` / `--all-scenarios` for the policy arms |
| `datagen/` | The generator package, one module per design document: `keys` (RNG discipline), `params` (single source of truth), `phase1`–`phase3` (the three phases), `world`, `scenarios` (the policy laboratory), `recording` (the recording layer), `export`, `validate` |
| `analyses/analysis_workbook.py` | Marimo workbook: builds a DuckDB database from the baseline arm, then EDA and a senior-analyst deep dive narrated for the owner (elasticities, promotion lift, stockout/spoilage economics, customer analytics, ML forecasting); run `uv run marimo edit analyses/analysis_workbook.py` |
| `analyses/catalog_walkthrough.py` | Marimo workbook: the graded walkthrough of `ANALYSIS_CATALOG.md` — one representative question per layer, answered from `visible/` and scored against the hidden answer key or a CRN-twin arm; run `uv run marimo edit analyses/catalog_walkthrough.py` |
| `data/scenarios/<name>/visible/` | One arm's analyst dataset: receipts (including voids and refunds), book-inventory snapshots, procurement invoices, price history, promotions, cost sheets, write-offs with stock-count corrections, tax statement, calendar, weather — realistically imperfect records; `documents/ACCOUNTING.md` defines what reconciles with what |
| `data/scenarios/<name>/hidden/` | That arm's answer key: customer parameters, demand modifiers and tilts, cost paths, budget paths, event log, the hidden-demand ledger (64k unmet-demand events across four causes), owner forecasts, the believed/realized/oracle profit triptych (pre- and after-tax), and the ledger of every injected data defect (`imperfections.csv`) |
| `data/scenarios/` | Every arm of the year, the **baseline included** (`baseline/` is the reference arm), plus CRN twins under edited macro scripts — war, typhoon, VAT reform, tax rebate, staffing — and `comparison.csv` across arms; run `uv run python generate_dataset.py --all-scenarios` |
| `main.py` | Entry point (placeholder) |

## Purpose

The primary objective is to generate a business dataset that supports four progressive layers of analysis, mirroring the natural flow of information in a business — from raw data collection through analytical processing to actionable insight and decision-making.

**1. Descriptive analysis** — understanding the current state of the business:

  * Data cleaning and manipulation
  * Feature engineering
  * Data visualization
  * Correlation analysis with explanatory models

**2. Diagnostic analysis** — investigating underlying causes and relationships:

  * Causal inference using Pearl's causal framework (the simulation's DAG is the ground truth)
  * Counterfactual analysis

**3. Predictive analysis** — forecasting:

  * Demand forecasting with machine-learning models

**4. Prescriptive analysis** — decision-making under constraints:

  * Inventory and pricing optimization using linear / mixed-integer programming

**Advanced analyses and modeling**

  * Hidden-demand modeling and unconstrained demand forecasting (from stockout-censored sales)
  * Conjoint / discrete-choice analysis for learning customer preferences (from simulated purchase choices)
  * Marketing Mix Model (MMM) development (from simulated promotion instruments — see Phase 3)

Collectively, these analyses address the core business questions that arise in any operational context:

  1. What is the current situation of the business? (Descriptive "IS" question)
  2. What factors tend to occur together in the business? (Correlation question)
  3. What is the cause of the observed phenomena? (Causal question)
  4. What is expected to happen in the future based on current patterns and trends? (Predictive question)
  5. What would have happened if an external intervention had been implemented? (Counterfactual question)
  6. What actions should be taken to maximize revenue under given conditions? (Optimization question)
  7. What can we do to learn customer preferences? (Intervention question)

By progressing systematically through these layers, the project illustrates how raw transaction data is transformed into strategic insights that directly support business decisions, reinforcing the intuitive and practical nature of data analytics.

## Technical requirements

  1. The simulation is written entirely in Python.
  2. The project splits across three executable artifacts: the original **Marimo design notebook** (SCM and MILP formulation), a plain reproducible **generator script** (`generate_dataset.py` — a stateful agent-based loop is clearer as a script than as reactive cells), and a **Marimo analysis workbook** for the interactive, analyst-facing side.
  3. **Data generation uses NumPy** (`numpy.random.Generator` seeded via `SeedSequence` streams keyed by stable identity — customer, SKU, day, receipt — so counterfactual replays are common-random-numbers valid). The simulation is a stateful, forward, agent-based process (inventory carries over, stockouts feed back into demand, the owner reacts to outcomes). **PyMC is reserved for the analysis notebooks**, where its probabilistic-inference capabilities belong (Bayesian explanatory models, causal estimation). This split also mirrors reality: the world that generates the data and the tools that analyze it are not the same.
  4. The owner's opening decision (location, assortment, quantities, staffing, prices) is solved as a MILP with **PuLP** (CBC solver); at this scale (~10 locations, ~709 SKUs) it solves in seconds.
  5. Comprehensive documentation lives in `documents/`: the three phase documents defend every distribution and parameter (support → generative story → maximum entropy), each contains its causal DAG, and `ACCOUNTING.md` specifies every money and goods flow together with the reconciliation contract the records obey.
  6. The generator validates itself on every run: 30 checks covering exact conservation identities, the tax arithmetic, forensic-realism fingerprints (charm-price mix, repricing cadence, revenue autocorrelation, seasonal patterns), and the recoverability of every injected recording defect — plus a structural-and-fingerprint subset for each scenario arm.

## Philosophy of the case design

The design is guided by a clear philosophy: present a simple yet meaningful scenario, explained thoroughly enough to be accessible to readers without a statistical or technical background. The simulation demonstrates three principles:

  1. Data analytics is not an esoteric discipline reserved for specialists; it comprises systematic practices employed daily by businesses of all sizes.
  2. Data collection, analytical reasoning, and decision-making form a natural progression that occurs in any business environment.
  3. The core concepts of data analytics are inherently intuitive — structured extensions of everyday business judgment.

A business frequently originates from a straightforward concept that expands rapidly as the owner confronts practical operational challenges. Consider an entrepreneur who opens a small grocery store to generate income for their family. The core idea fits in one sentence, but implementing it requires answering several essential questions:

  1. Where should the shop be located? (This determines monthly fixed costs such as rent.)
  2. What products should the shop offer? (This shapes the product portfolio, inventory management, storage requirements, variable costs, and the associated optimization problems.)
  3. How should inventory be replenished, managed, and maintained? (Inventory optimization and demand forecasting.)
  4. Which information should be recorded, and in what format? (Performance tracking, accounting, and compliance.)
  5. How much initial capital is available? (This constrains the scale of operations and financial planning.)

These questions, though seemingly elementary, are critical to business viability. Each can be formulated as an optimization, explanatory, or predictive problem — and each often admits a straightforward solution once the business context and underlying drivers are understood.

Accordingly, the simulation is built around a small neighborhood grocery store that opened one year ago and has operated for 12 months. The case shows how routine business decisions naturally generate data that can be analyzed into actionable insights.

The analytical process begins with the systematic recording of business activities — *what* occurred, *where*, and *when*. These transactional records are the raw data virtually every business produces: voluminous, noisy, and requiring careful processing — accurately reflecting the daily reality faced by managers, accountants, and analysts.

## Simulation process

The system is built bottom-up from microeconomic elements — customer preferences, location characteristics, and the owner's decision process — whose interactions create the aggregate forces of supply and demand, perturbed by stochastic factors such as weather and market shocks. The economic behavior follows concrete rules throughout: demand curves slope downward (price increases reduce quantity demanded according to each customer's price sensitivity), customers respect their budget constraints, and substitution occurs within categories when preferred items are unavailable or too expensive.

Construction proceeds in three phases.

### Phase 1 — Basic components of the system

  * **Supply side:** the owner profile, with a fixed initial budget.
  * **Demand side:** the set of candidate locations (each with rent and neighborhood characteristics) and the customer profiles (preferences and budgets) of people living near each location.

The owner's budget constrains the location choice and initial inventory; the customer profiles determine individual budgets and consumption choices, which aggregate into the latent demand of the location. Together these establish available supply and latent demand, waiting for interaction and realization.

Each customer profile has a fixed weekly schedule — they shop for groceries only on certain days of the week, with a small probability of deviation. For example, a customer usually restocks on Saturday or Sunday, but occasionally needs something mid-week and drops by. Customer demand is realistic: each has a weekly shopping list spanning categories such as food and drink, hygiene, and household cleaning products, plus items that appear randomly depending on circumstances.

This phase produces one owner profile and many customer profiles — the pool of potential customers near the chosen store location.

### Phase 2 — Stochastic elements at the macro level

  * **Seasonal effects on demand:** season shifts individual demand for certain goods in certain periods (e.g., ice cream demand is higher in summer, lower in winter). Weather (temperature, precipitation) modulates both foot traffic and category demand day to day.
  * **Supply shocks from macro factors:** events such as war or energy shortages raise the cost of certain goods. Customers react to the resulting price increases according to their preferences and budgets.
  * **Idiosyncratic shocks at the individual level:** shocks that shrink or expand an individual customer's budget, affecting that period's consumption.

These stochastic factors introduce noise that makes the data realistic and hard to work with. From the owner's perspective they are business risk, complicating the optimization problem and forcing the owner to account for them when refinancing to keep the store running.

### Phase 3 — Market interaction

The simulation runs on a daily basis; each day has a day-of-week, day-of-month, and season, and is affected by the predetermined shock paths from Phase 2. Each visit draws an arrival hour from a two-peak daily profile (after-work on weekdays, late morning on weekends); predetermined and stochastic events then unfold:

  * The owner sets opening and closing hours (predetermined). Customers may arrive outside opening hours and be turned away — these lost visits are one source of **hidden demand**.
  * Whether a customer arrives in a given hour is random, and which customer arrives is also random. Once selected, the customer acts according to their predetermined preferences, with a small probability of deviation. Sales draw down the owner's stock; when demand cannot be met from available supply (stockouts), it creates hidden, constrained demand — recorded internally as latent truth, invisible in the sales data.
  * Periodically the owner restocks and performs a cost–revenue optimization. This is deliberately solved as an *imperfect* optimization (a heuristic minimum-inventory rule tied to location characteristics — see the SCM in the notebook), leaving room for the analyst to find genuine improvements later. The owner can also run **promotions** (temporary discounts, flyers, a loyalty discount day) to clear inventory; customers respond to price changes according to their price sensitivity. Promotion timing, depth, and cost are recorded, providing the marketing instrument data required for the Marketing Mix Model.
  * Customers pay by cash or card according to their profile: a customer who prefers card pays by card most of the time (e.g., 95%) and by cash otherwise, and vice versa. **Card transactions carry customer identity (a hashed POS token); cash transactions are anonymous.** A stream of one-off **guest** shoppers with single-use tokens passes through as well. This is the dataset's realistic missing-data mechanism: customer-level analysis is only partially possible, exactly as in real retail data.
  * Occasionally a customer brings an item back: **refunds** post as their own till transactions (negative quantity, refunded at the price actually paid, referencing the original receipt via `ref_receipt_id`). Money flows backwards through the till and the monthly ledger; the returned item is destroyed, not restocked.
  * Finally, everything above passes through a **recording layer** before export: the shop's *paperwork* errs even though its physics doesn't. Receipts get re-uploaded by POS retries, invoices get double-posted or never entered, spoilage gets tossed without logging (surfacing later as month-end stock-count shrinkage), a clerk mistypes the odd shelf count, payment labels drift, the weather sensor goes dark for a few days. Every defect is injected from its own keyed stream, logged to a hidden ledger, and provably cleanable — the data-cleaning exercise is graded, not decorative.

### Recorded data (what the analyst receives)

  * Receipt line items (date, hour, SKU, quantity, price paid, promo flag, payment method, customer token for card payments only, `ref_receipt_id` on refunds) — including the till's warts: voided mis-rings, duplicate uploads, placeholder timestamps
  * Nightly **book-inventory** snapshots and procurement invoice lines (order, delivery, and posting dates)
  * Write-off log: recorded spoilage plus monthly stock-count shrinkage corrections, labeled by reason
  * Promotion log (category, discount depth, start/end dates, flyer cost)
  * Shelf-price history, the owner's monthly ledger (revenue net of refunds, procurement, rent, wages plus payroll tax, utilities, storage, flyers, VAT remittance, credit line), and the annual tax statement
  * Calendar and weather table (date, day-of-week, season, holiday flags, temperature, precipitation — with a few sensor-outage gaps) — the *effects* of weather remain hidden; only the observable conditions are shared

`documents/ACCOUNTING.md` documents every one of these flows and the reconciliation contract between them (what ties to the cent after which cleaning step, and which gaps are supposed to remain).

What the analyst does **not** receive: customer preference parameters, true demand functions, shock effect sizes, the owner's decision rules, unmet-demand records, and the defect ledger. These constitute the ground truth against which the analyses can be validated.

## Known limitations and deliberate design choices

  * **One seasonal cycle.** Twelve months of history yields 52 weekly cycles (ample for weekly patterns) but only a single annual cycle, so annual seasonality cannot be reliably learned by forecasting models. This is realistic for a one-year-old business and is itself a teachable point; a later iteration may extend the horizon to 24–36 months.
  * **Suboptimal owner by design.** The owner's heuristic inventory rule and simple markup policy leave measurable money on the table (the oracle replay prices the gap at roughly €7.6k for the reference year), so the prescriptive layer has a genuine optimization gap to find.
  * **Partial customer identifiability.** Only card transactions link to customers — a deliberate, realistic missing-data mechanism, verified MAR in this iteration so the analyst's own missingness test passes.
  * **No supplier dimension.** Invoices cannot be attributed to individual vendors; posting batches and cost shocks are observable but not vendor-linked.
  * **Fixed assortment and delivery cadence.** The 128 stocked SKUs and the weekly Wednesday delivery never change all year — protecting the censored-demand evidence and keeping the panel clean.
  * **Simple financial plumbing.** Procurement is cash-basis at order date (no payment terms or accounts payable); refunds are destroy-on-return of one line, with no fraud or restocking.

## Roadmap

  1. **Iteration 1 — done:** SCM and owner's MILP, location and SKU tables, the opening decision (Phase 1).
  2. **Iteration 2 — done:** customer profiles and demand model; the daily market loop over 12 months; recorded-data export; stochastic cost paths, weather, and macro events (Phases 2–3).
  3. **Iteration 3 — done:** promotions and MMM instrumentation, the owner's adaptive weekly behavior, the oracle counterfactual — plus additions beyond the original plan: guest shoppers, menu-cost repricing, weather-linked spoilage, the recording layer of realistic data defects, refunds, and the accounting documentation.
  4. **Iteration 4 — done:** the policy laboratory (Phase 4): the tax layer (differential VAT with a tax-aware but non-strategic owner, payroll contributions, profit tax) and CRN-twin scenario arms with the baseline as one arm among them.
  5. **Analysis notebooks (next):** one per analytics layer, validated against the hidden ground truth.
