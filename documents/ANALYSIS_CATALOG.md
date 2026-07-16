# The Analysis Catalog — Questions This Data Can Answer

Every question below is answerable from an arm's `visible/` folder, and — this
is the point of the whole project — **gradeable**: the generating mechanisms
are recorded in `hidden/`, and the scenario arms are CRN twins of the baseline,
so both estimates *and methods* can be scored against ground truth. Questions
are grouped by analytics layer, in the order a real engagement would tackle
them; each layer maps onto the README's seven core business questions (noted
per section).

How to read the tables: **Question** is phrased the way the owner would ask
it; **Approach** names the method a competent analyst would reach for;
**Graded against** names the truth. "Twin diff" means the causal answer is the
literal difference between two CRN-twin arms in `data/scenarios/`.

**Applicability across arms.** Every question in Layers 0–4 and 6 applies to
*every* arm, not just the baseline: each scenario folder is a complete
instance of the same world — same schemas, its own recording-layer defects,
its own tax accounting, and its own full `hidden/` answer key exported from
its edited script — so each question is askable of, and gradeable against,
any arm. The *answers* differ by arm, which is itself analyzable (a cleaning
pipeline built on the baseline should transfer to the war arm unchanged; the
elasticities should not). Layer 5 is the one exception: its questions are
about arm *pairs* by construction. Some questions are sharpest in a specific
arm — pass-through (2.3) in `food_vat_cut_july`, elasticity identification
(2.4) in `war_june`, stockout prediction (3.4) in `second_clerk`.

The **three-year arms** (`3y_baseline` and its twins, P5) run everything in
Layers 0–4 and 6 on a longer clock — three recording-layer binders to clean,
three Christmases to describe, three cost-shock episodes to diagnose — and
additionally unlock **Layer 7**, the questions a single year structurally
cannot ask: trend, churn, structural breaks, regime-change forecasting, and
capital decisions. Year one of `3y_baseline` is byte-identical to
`baseline/`, so any pipeline built on the baseline must reproduce its own
numbers there before extending — a built-in regression test for the
*analyst's* code.

---

## Layer 0 — Clean the records before trusting them

*The recording layer (P3 §20) planted ten defect families; every find is
gradeable row-by-row against `hidden/imperfections.csv`, and the
reconciliation contract lives in `ACCOUNTING.md` §9.*

| # | Question | Approach | Graded against |
| --- | --- | --- | --- |
| 0.1 | Which receipts were uploaded twice, and what was revenue *really*? | the all-even multiplicity rule; reconcile deduped receipts to `cost_sheet.revenue` | `imperfections.csv` (`dup_receipt`); tie to the ledger to the cent |
| 0.2 | Which negative till lines are cancelled mis-rings, and which are real refunds? | partition by `ref_receipt_id`; match void partners within receipts | `void_pair` rows; refund referential integrity |
| 0.3 | Do supplier invoices reconcile to the ledger's procurement line? | exact-key dedup; explain the residual gap | `dup_invoice` + `missing_invoice` rows |
| 0.4 | Does book stock reconcile with the paperwork, night by night? | perpetual-inventory identity per SKU-day (refund lines excluded) | `snapshot_typo` rows: breaks come in next-day pairs |
| 0.5 | What is "shrinkage" here, and what causes it? | decompose `write_offs` by `reason`; trace `stock_count` corrections back to document defects | `unrecorded_spoilage` rows dominate the drift |
| 0.6 | Standardize the label mess | payment-label normalization, hour-0 placeholder handling, the promotions category typo, weather sensor gaps | `payment_variant`, `hour_glitch`, `category_typo`, `weather_outage` rows |
| 0.7 | After cleaning: which totals should tie exactly, and which gaps are *supposed* to remain? | run the full reconciliation contract | `ACCOUNTING.md` §9 line by line |

## Layer 1 — Describe the business (core questions 1–2: the "IS" and correlation questions)

| # | Question | Approach | Graded against |
| --- | --- | --- | --- |
| 1.1 | Where does the money come from and go? | P&L from `cost_sheet`; margin waterfall incl. VAT and the tax statement | ledger identities (§7 of ACCOUNTING) |
| 1.2 | When do people shop? | day-of-week / hour-of-day profiles, weekday vs weekend regimes | emergent from P1 schedules — the trap: these are schedule composition, not day preferences |
| 1.3 | What sells when? | monthly seasonality indices per category and product type (ice cream vs the frozen aggregate) | `demand_modifiers.csv`, `tilts.csv` |
| 1.4 | What does a basket look like? | basket size/value distributions, category co-occurrence, impulse share | P3 basket mechanics |
| 1.5 | Who are the customers? | RFM segmentation of the card panel; regulars vs one-off guests vs anonymous cash | `customers.csv`, `guests.csv` |
| 1.6 | How are prices architected? | charm-ending mix, repricing cadence, markdown depth menu | P1 §8 / P2 §9 parameters |
| 1.7 | How often are shelves empty, and what rots? | OOS incidence by SKU-month; write-off seasonality | inventory truth via conservation identity |
| 1.8 | How much tax does the shop handle? | effective VAT rate by category group; remittance seasonality | `PHASE4` rates |

## Layer 2 — Diagnose causes (core question 3)

| # | Question | Approach | Graded against |
| --- | --- | --- | --- |
| 2.1 | Does weather move the business? | regression of visits/revenue on rain and temperature anomaly with calendar controls, HAC errors, next-day rebound lags | `weather_full.csv` (true anomaly), P2 traffic coefficients |
| 2.2 | What hit costs in October? | event-study on invoice cost indices by category | `event_log.csv`, `cost_paths.csv` |
| 2.3 | How much of a cost shock reaches the shelf, and how fast? | pass-through regression of tags on invoice costs; hysteresis/asymmetry tests | the menu-cost rule (EWMA α, 3% band) is the documented truth |
| 2.4 | Does raising a price lose customers or just move them? | SKU-level IV elasticity (cost-path instruments) vs category-level two-way FE — substitution vs walkaway | `customers.csv` price sensitivities; choice-model structure |
| 2.5 | Is my instrument valid? | test the energy crisis as an instrument (it also squeezes budgets → invalid) vs idiosyncratic cost events (valid) | P2 §17.4 — instrument validity is itself a planted lesson |
| 2.6 | Did the markdowns work? | naive lift vs DiD vs selection-aware estimates; the loyalty Sunday as the clean exogenous anchor | overstock-triggered selection is the planted bias; loyalty lift is the clean pulse |
| 2.7 | Why does food rot faster some weeks? | write-off regression on temperature and the crisis timeline | `spoil_factors.csv` |
| 2.8 | Can I trust card data to represent everyone? | test the missingness mechanism (card vs cash baskets, composition) | MAR by design in this iteration — the test should *pass* |
| 2.9 | What drives refunds and shrinkage? | rate modeling over time/category; year-end refund censoring artifact | refund mechanism (P3 §21); `imperfections.csv` |
| 2.10 | Do pre-holiday days really spike? | small-N inference done honestly (9 days/year) | P2 loadings' h_c column |

## Layer 3 — Predict (core question 4)

| # | Question | Approach | Graded against |
| --- | --- | --- | --- |
| 3.1 | What will next week sell? | category demand forecasting vs the seasonal-naive benchmark, judged at the weekly decision grain | held-out quarter; `demand_modifiers.csv` |
| 3.2 | What would demand be if shelves never emptied? | censored-demand modeling: impute stockout-lost sales | `hidden_demand.csv` — 64k events across four causes |
| 3.3 | How wrong is the owner's own forecast, and why? | autopsy the trailing-MA rule; quantify the censoring spiral | `owner_forecasts.csv` vs realized and vs true demand |
| 3.4 | Which SKUs will stock out next week? | OOS risk classification from cover, seasonality, delivery cadence | subsequent weeks' truth |
| 3.5 | Which regulars are sliding into trouble? | early-warning detection of sustained down-trading spells | `spell_flags.csv`, `budget_paths.csv` |
| 3.6 | How far can one year of history be trusted? | quantify the single-seasonal-cycle limit (one Christmas, one summer) | honest epistemics — and now priced empirically: fit on the baseline year, test on `3y_baseline`'s later years (7.5) |

## Layer 4 — Prescribe (core question 6)

| # | Question | Approach | Graded against |
| --- | --- | --- | --- |
| 4.1 | What is better analytics *worth*, in euros? | rebuild the ordering policy on de-censored, seasonality-anticipating demand; close the believed/realized/oracle gap | `profit_triptych.csv` — the oracle prices the ceiling |
| 4.2 | How should perishables be ordered? | spoilage-aware cover per category (waste vs stockout trade-off) | the oracle's smooth perishable buffer rule |
| 4.3 | Where is margin safely adjustable? | category-level repricing using the elasticity structure (safe at category, self-defeating at SKU) | choice-model truth; scenario replay possible |
| 4.4 | What should be delisted or added? | dead-SKU economics: appeal, storage, listing fees | `decision_t0.csv`, appeal is hidden by design |
| 4.5 | When should promotions run, on what, how deep? | redesign the markdown trigger with selection bias removed | lesson #3 machinery |
| 4.6 | Should I hire and extend hours? | cost-benefit of recovered `closed`-cause demand vs employer-priced labor | the `second_clerk` arm **is** the answer |
| 4.7 | How much cash must the till hold? | working-capital policy: credit line, VAT remittance timing, the tax jar | ledger mechanics (ACCOUNTING §7) |

## Layer 5 — The policy laboratory (core question 5: counterfactuals)

*Each scenario arm is a CRN twin: the arm-vs-baseline difference is the causal
effect with zero sampling error between arms. The deepest exercise in each row
is the **method validation**: estimate the effect observationally inside one
arm, then check yourself against the twin diff.*

| # | Question | Arm | What the twin diff reveals |
| --- | --- | --- | --- |
| 5.1 | Who actually bore the food-VAT cut — customers or the owner? | `food_vat_cut_july` | tax incidence split; pass-through speed and completeness through menu costs |
| 5.2 | What did households do with the rebate? | `tax_rebate_spring` | an emergent marginal propensity to consume; where budget constraints actually bound |
| 5.3 | What does a broad supply shock do to a grocer? | `war_june` | revenue up, units down — demand destruction decomposed by category resilience |
| 5.4 | What does a storm cost, net of the catch-up? | `typhoon_september` | intertemporal substitution via pantries; the storm's true (small) annual cost |
| 5.5 | Does my observational elasticity generalize? | any cost-shock arm | external validity: predict the twin's outcome from baseline-estimated structure |
| 5.6 | Was hiring the clerk worth it? | `second_clerk` | full-cost staffing counterfactual, payroll tax included |

## Layer 6 — Advanced and structural (core question 7: learning preferences)

| # | Question | Approach | Graded against |
| --- | --- | --- | --- |
| 6.1 | What do customers *want*? | discrete-choice (conditional logit) estimation on the card panel: price sensitivity, brand affinity distributions | `customers.csv` — per-customer true parameters |
| 6.2 | Can partial pooling beat per-SKU noise? | hierarchical Bayesian demand models (the PyMC layer) | SKU/category truth at every level |
| 6.3 | What drives sales, decomposed? | MMM: base, seasonality, weather, price, promotions, events | `demand_modifiers.csv`, `tilts.csv`, `event_log.csv`, promo log |
| 6.4 | Where did the missing demand go? | structural four-cause decomposition (closed / stockout / budget / outside) | `hidden_demand.csv` cause labels |
| 6.5 | How much business is passing trade? | mixture modeling of the token panel: regulars vs single-use guests | `guests.csv` |
| 6.6 | Is the documented causal graph consistent with the data? | test the DAG's implied conditional independencies | the DAGs in PHASE1–3 details |

## Layer 7 — The three-year arc (P5: time, churn, and capital)

*Asked of `3y_baseline` (`data/scenarios/3y_baseline/`), graded against its
`hidden/` key and the `3y_no_competitor` / `3y_no_expansion` CRN twins. These
are the questions one year of data structurally cannot ask.*

| # | Question | Approach | Graded against |
| --- | --- | --- | --- |
| 7.1 | Is the business growing, or is it just summer? | trend–seasonality decomposition (STL / year-over-year indices) now identified with three annual cycles | `demand_modifiers.csv` is mean-one *per year* by construction, so measured trend must come from the panel and inflation — `customers.csv` arrival/departure dates + `cost_paths.csv` |
| 7.2 | Which customers left, which arrived, and who was never going to stay? | churn inference from token silence (competing risks: lapsed vs gone), cohort retention curves, survival modeling | `customers.csv` — `arrival_date`, `departure_date`, `persistence`; survivorship bias in loyalty metrics is the planted trap (lesson #11) |
| 7.3 | What happened in March 2027? | structural-break detection on visits/revenue; then *who* left — defection concentrated among price-sensitive transients | the competitor script (entry date, ramp, χ); `3y_no_competitor` twin diff prices the entry (~€5k net over 2027) |
| 7.4 | Did customers trade up after the discounter opened? | premium share and basket value rise post-entry — composition vs behavior decomposition | nobody traded up: the price-hunters left (lesson #12); `persistence` + departure dates prove the mix shift |
| 7.5 | Does a model trained on 2025–26 survive 2027? | true holdout-year evaluation; forecast breakdown at the regime change, monitored vs unmonitored | the held-out year itself + the `3y_no_competitor` twin separating regime break from model error (lesson #16) |
| 7.6 | Did the promotions of 2027 work? | naive promo lift vs entry-aware estimates — the owner cut prices and loosened markdowns *because* revenue fell | the response is scheduled off the entry script, absent in `3y_no_competitor` (lesson #14: the endogenous-response confound) |
| 7.7 | What do the three cost-shock episodes have in common? | compare pass-through of the 2025 energy crisis, 2026 avian flu, and 2027 commodity spike — same menu-cost mechanics, different competitive regimes | `event_log.csv`, `cost_paths.csv`, the response's markup cut in `price_history.csv` |
| 7.8 | What did the freezer failure, the apartment block, and the festival each cost or earn? | event studies on narrated one-offs: a `damage` write-off spike, a demand step, a guest surge | the P5 script parameters (dates, magnitudes); `write_offs.reason`, `guests.csv`, arrival dates |
| 7.9 | Was the expansion a good investment? | capital budgeting from the books: capex, the clerk's wages, extended-hours revenue, recovered stockouts — NPV the bet | `3y_no_expansion` twin: the bet costs ~€82k over its life (lesson #13, investment at the peak) |
| 7.10 | How does capital actually flow through a small shop? | financial-statement analysis of the widened cost sheet: retained earnings, owner draws, the January tax cash calls, the rent step, wage revisions | ACCOUNTING §7.1's P5 columns and the contract schedule; the RE ledger reconciles to the cent by construction |
| 7.11 | Renew the lease or close? | the capstone prescriptive: decompose 2027's −€2k into expansion, entry, and contract steps, then project 2028 under renewal | both twins together — the decomposition has a known answer: the expansion (−€82k) dwarfs the discounter (−€5k) |


---

## Coverage of the README's seven core questions

| Core question | Catalog sections |
| --- | --- |
| 1 — current situation (descriptive) | Layer 1 (after Layer 0's cleaning) |
| 2 — what co-occurs (correlation) | 1.2–1.4, 2.1 |
| 3 — causes (causal) | Layer 2 |
| 4 — forecasts (predictive) | Layer 3 |
| 5 — interventions (counterfactual) | Layer 5; 7.3, 7.9, 7.11 (the P5 twins) |
| 6 — optimal actions (optimization) | Layer 4; 7.9–7.11 (capital decisions) |
| 7 — learning preferences (intervention/structure) | Layer 6 |

Layer 7 cuts across the core questions rather than adding an eighth: it is
the same seven asked over *time* — growth vs season, churn, breaks, regime
change, and the owner's capital story.

A natural notebook series follows the layers in order — cleaning first (its
output feeds everything), the policy laboratory after diagnosis (5.5's method
validation needs Layer 2's estimates), structure last, and the three-year arc
(Layer 7) as its own arc-length engagement once the one-year pipeline is
trusted (its year one doubles as that pipeline's regression test).
`analyses/analysis_workbook.py` walks a single narrative through Layers 0–4
at survey depth; `analyses/catalog_walkthrough.py` demonstrates the grading
loop with one scored question per layer; Layer 7 is covered by its own
trio — `analyses/three_year_review.py` (7.1–7.5, 7.10–7.11 posed),
`analyses/competitor_entry_study.py` (7.3–7.6), and
`analyses/expansion_review.py` (7.9, 7.11 answered). The catalog is the
specification for doing each layer at full depth, graded.
