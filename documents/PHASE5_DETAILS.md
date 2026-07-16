# Phase 5 — Three Years: Growth, Churn, and the Unquiet World

*(2026-07-16. Builds on Phases 1–4; extends the horizon, adds the panel flow and
the owner's balance sheet, and scripts years two and three. Changes to the
year-one exogenous script are forbidden — see the identity contract, §2.
**Implemented 2026-07-16**: the three-year world generates as the scenario arms
`3y_baseline`, `3y_no_competitor`, and `3y_no_expansion` under
`data/scenarios/` — the `3y_` prefix keeps them apart from the one-year arms —
and passes the full P5 validation battery; measured reference numbers appear
in §15.)*

Phases 1–4 produced one performed year and a laboratory for replaying it. One
year is a photograph: it cannot separate trend from seasonality, it cannot show
a customer arriving or leaving, and its owner never faces the question every
real shopkeeper faces — *reinvest, hold, or quit*. Phase 5 turns the photograph
into a film. The horizon becomes three years (2025-01-01 .. 2027-12-31,
$t = 1..1095$), and three new kinds of motion enter the world:

1. **The customer panel becomes a flow** — people move into the neighborhood
   and out of it, and the store's history is written by who stayed.
2. **The owner accumulates retained earnings** and, when they cross a
   threshold, expands the shop — an endogenous investment decision with an
   honest, uncertain payoff.
3. **The world stays unquiet.** Year one is the baseline — the least exciting
   year, the bare minimum of what a first year can be. Years two and three are
   scripted with shocks whose impacts are *not* what the owner anticipates:
   a freezer dies, an apartment block fills, a discounter opens, a festival
   arrives, contracts reprice. Life does not hold still, and neither does
   this dataset.

**The governing principle is unchanged from Phase 4:** agents never see "the
script." Customers see prices, budgets, and the new discounter's flyers; the
owner sees invoices, tills, and a rent letter. Every aggregate consequence —
growth, defection, margin squeeze — *emerges* from Phase 1–3 behavior replayed
through the keyed-RNG market loop.

---

## 1 Why three years, and what each buys

| Year | Name | Role in the dataset |
|---|---|---|
| 2025 | **Proof of concept** | The published baseline's script, replayed with a live panel (churn from month one, §2). Energy crisis, one wage raise, random events — the "least excited" year that sets expectations. |
| 2026 | **Growth, with scares** | The neighborhood grows, the owner's capital grows, and both are interrupted: a freezer failure, a supply shock, a heatwave. Ends with the expansion — the owner's bet on the future. |
| 2027 | **The squeeze** | The rent reprices, a discounter opens, the owner fights back, a festival gives one good fortnight, a commodity spike lands. Ends on the question the whole dataset was built to pose: *was the expansion right, and is the shop worth continuing?* |

Analytically, the second and third year unlock questions the catalog could not
previously ask: trend–seasonality separation, year-over-year decomposition, a
true holdout year for forecasting, cohort and survival analysis, structural
breaks, and the external validity of every year-one causal estimate.

## 2 The identity contract (the script is sacred; the people are not)

*(Amended 2026-07-16 after the independent-analyst audit of the first
vintage. The original contract froze the customer panel through all of 2025
so that year one of the three-year run stayed byte-identical to the published
one-year baseline. The audit showed that freeze was the dataset's single most
visible artifact — not one regular went silent in twelve months, then dozens
did — and realism won: the panel now flows from month one.)*

> **Contract.** Restricted to dates ≤ 2025-12-31, every **exogenous-script**
> artifact of the three-year baseline run — calendar, weather, demand
> modifiers and tilts, cost and rate paths, spoilage factors, the event log,
> locations, the opening decision — is **byte-identical** to the one-year
> baseline run's. The **endogenous** artifacts (receipts, inventory,
> procurement, write-offs, prices, forecasts) are *near* the baseline but not
> identical: the panel churns from day one, so the people differ even while
> the world's script stands still. The published one-year arm itself is
> untouched — it remains its own, separately validated dataset.

This split is exactly what the keyed-RNG discipline (P2 §13) buys: panel
draws live under their own `K_PANEL` keys, so adding year-one churn moves no
weather draw, no cost path, no event. The remaining implementation rules:

- **Churn from month one.** Original transients face the monthly hazard from
  the first close (`churn_start_month = 1`); replacements and the growth
  trickle run in year one too.
- **No owner draw in year one.** The founder lives off savings while proving
  the shop (§4).
- **The recording layer runs per calendar-year block**, keyed by year.
- **Refunds deferred past 2025-12-31** — dropped in the one-year run —
  materialize in January 2026: year two opens with a handful of refunds
  referencing December sales, a realistic seam.

**Validation #31** checks that the exogenous-script files' year one is a
byte prefix of the published baseline's — the CRN guarantee, stated on the
files an analyst can diff.

## 3 The panel flow: rooted and transient customers

Every regular receives, at creation, a **persistence type** drawn from a new
keyed stream (`K_PANEL = 10`):

$$
\text{type}_i =
\begin{cases}
\text{rooted} & \text{w.p. } 0.80\\
\text{transient} & \text{w.p. } 0.20
\end{cases}
$$

**Rooted** customers are the long-term residents — people who will not change
where they live within the three-year window. By construction their departure
hazard is zero inside the horizon. **Transient** customers come and go: each
faces a monthly departure hazard

$$
h = 1/18 \quad (\text{mean tenure } 18 \text{ months}),
$$

drawn at each monthly close from `rng_for(K_PANEL, customer, month)`. At the
panel level this yields roughly $0.20 \times 12/18 \approx 13\%$ annual
turnover — brisk enough to matter, slow enough for a neighborhood store.

**Replacement and growth.** The neighborhood does not empty out, but it also
does not boom:

- Each departure is matched by a replacement arriving $1 + \text{Geometric}(0.5)$
  months later (usually the next month) — a household moving into the vacated
  flat. Replacements are fresh Phase 1 profile draws (budget, adherence,
  price sensitivity, brand taste, primary day) under `K_PANEL` keys, with a
  fresh pantry initialized by the standard $t_0$ draw.
- Newcomers skew mobile: their persistence mix is **50/50** rooted/transient
  (people who just moved are likelier to move again).
- On top of replacement, a **trickle of net growth**: $\text{Poisson}(4)$
  extra arrivals per year (the neighborhood grows really slowly), plus one
  scripted step — the apartment block of §7 (year two).
- **Guest intensity scales with the panel**: the daily guest Poisson mean is
  multiplied by $N_t / N_0$ (current regulars over opening regulars), so the
  anonymous stream grows with the neighborhood too.

**What the analyst sees.** Nothing explicit. A card token simply stops
appearing; a new token starts. The visible data never says "moved away" — the
analyst must infer churn from silence, and must not confuse a departed
customer with a lapsed one (the down-trading spell detector of the workbook
now has competing risks). The answer key (`hidden/customers.csv`) gains three
columns: `arrival_date`, `departure_date` (empty if still present),
`persistence`.

**Pantry bookkeeping.** A departing customer's pantry state is deleted the day
after their last month ends; their scheduled refunds still resolve (a person
returns a broken jar even in moving week — and the refund lag is ≤ 13 days, so
no orphan refunds arise).

## 4 Retained earnings and the expansion

### 4.1 The books formalize in January 2026

In year one the owner takes nothing out of the till: a founder proving a shop,
eating from savings. From the January-2026 close onward he pays himself, and
what he does not pay himself is **declared retained earnings** — capital
earmarked for the store:

- **Opening balance.** At formalization, everything the first year actually
  earned becomes the opening RE balance:
  $\text{RE}_0 = \text{(year-one after-tax result)} \approx € 29{,}183$
  (this vintage). It is a bookkeeping declaration — no cash moves.
- **Monthly retention.** At each close from January 2026, with $\pi_m$ the
  month's after-tax result:
  $$
  \text{draw}_m = (1 - \rho_{RE}) \cdot \max(0, \pi_m), \qquad
  \text{RE}_m = \text{RE}_{m-1} + \rho_{RE} \cdot \max(0, \pi_m) - \text{capex}_m,
  $$
  with retention ratio $\rho_{RE} = 0.5$. The draw leaves cash at the close
  (after rent, wages, VAT, interest — before the credit-line sweep). In a loss
  month there is no draw: the owner tightens his belt, and RE absorbs nothing.
- **Profit tax actually paid.** The Phase 4 idealization ("accrued, paid next
  January, cash never moves") ends: the prior year's profit tax **leaves cash
  at the January close** of 2026 and 2027. It hits Q1 cash exactly when a real
  small business feels it.

`cost_sheet.csv` gains six columns: `year`, `repairs`, `owner_draw`,
`retained_earnings` (the running balance), `capex`, `profit_tax_paid`. The
`month` column stays the integer 1–12 it always was — the published one-year
baseline keeps its schema untouched, and the three-year sheet is addressed
by (`year`, `month`) (implementation amendment).

### 4.2 The expansion decision

At each monthly close from 2026 on, if the shop has not yet expanded and

$$
\text{RE}_m \geq K_{exp} \quad \text{and} \quad
\text{cash}_m - \text{tax\_reserve}_m \geq C_{exp},
$$

the owner expands **on the first day of the following month**:

| Lever | Before | After |
|---|---|---|
| Hired staff | owner alone (the MILP hired nobody) | **one clerk on a fixed 8-hour shift** — the first hire is part-time peak cover, not a full-open-hours position (implementation amendment: at an 18% gross margin, a clerk paid for all 14 open hours would consume ~70% of the shop's entire margin, which no owner would sign) |
| Opening hours | 08–20 | **07–21** (+2 h/day) |
| Shelf capacity | $S$ | $1.2\,S$ (deeper stock, same assortment) |
| One-off capex | — | $C_{exp} = €14{,}000$ from cash and RE (shelving, a second till, a cold cabinet, fit-out) |

The assortment does **not** widen — the fixed-assortment contract (P3 §19.3)
survives, and with it the censoring-spiral evidence. Growth is depth and
hours, not breadth. Exactly one expansion is possible per run: a second
threshold exists in the params but is not reachable in this script, which
keeps the mechanism honest in the code.

**Calibration target, not hard-coded date.** $K_{exp} = €52{,}000$ (calibrated;
the first draft's €45k fired in spring) is chosen so that, in the realized
baseline path, the crossing lands in **autumn 2026** — after the apartment
block fills (§7), before the discounter opens (§8). In the realized path the
trigger crosses at the October close and the expansion executes **November 1,
2026**, with RE at €40.8k after the capex. The February freezer failure
debits RE by the repair and the written-off stock's cash echo, *visibly
delaying the crossing* — a causal chain the analyst can narrate from the cost
sheet alone. If a code change moves the profit path, retune $K_{exp}$ to keep
the autumn-2026 landing; the date is emergent, the season is designed.

**Is the expansion a good idea?** Measured answer: **no — and that is the
lesson.** Ex ante it is the natural move: a year and a half of accumulating
surplus, a neighborhood that just grew, December about to peak. Ex post the
`no_expansion` twin (§9) prices the bet at roughly **−€82k over its
fourteen-month life** (three-year realized profit €83k with the expansion,
€165k without): the clerk's wages and payroll tax plus the capex overwhelm
what the two extra opening hours and the deeper shelf bring in at an 18%
margin, and then the discounter lands on top. *"The owner invested at the
peak"* is planted lesson #13 — the most common capital mistake in small
retail, reproduced from first principles: labor is bought at market wage,
margin is earned at grocery rates, and optimism does the rest.

## 5 Contracts and nominal drift

Prices already drift: Phase 2's continuous inflation ($2.5\%/\text{yr}$,
$\text{infl}(t) = e^{0.025\,t/365}$) keeps riding supplier costs, utilities,
and storage over all three years (≈ +7.8% cumulative). Phase 5 adds the
*lumpy* nominal world on top — the world of contracts, which reprice in steps,
on dates, with memory:

| Item | Mechanism | Schedule |
|---|---|---|
| **Rent** | 2-year contract, then renewal at market | €1,160.66/mo through 2026-12; **+12%** from 2027-01 (≈ 5% inflation catch-up + 7% market reprice: the landlord watched the shop succeed) |
| **Wages** | statutory minimum-wage revisions, each July | +4% at $t{=}182$ (existing, untouched); **+4% at $t{=}547$** (2026-07); **+5% at $t{=}912$** (2027-07, tight labor market) — ≈ +13.6% cumulative |
| **Utilities tariff** | annual contract resets, each January, on top of `infl` and usage | **+6% at $t{=}366$** (2026-01: energy-crisis aftermath repricing); **+3% at $t{=}731$** (2027-01) |
| **Storage / misc** | rides `infl` | unchanged |
| **Supplier costs** | ride `infl` + events | unchanged |
| **VAT rates** | constant | unchanged (scenarios may still vary them) |

Rent becomes a *schedule* `rent(t)` instead of a constant; wage raises become
a list; the utility tariff multiplies into `utility_rate`. The menu-cost
hysteresis will translate drifting costs into slightly more frequent
repricing — the 3–15 changes/yr validation band is re-checked per year and
widened only if a year genuinely needs it.

## 6 Year one — 2025, "Proof of concept"

Untouched, by contract (§2). The energy crisis (scripted, $t{=}274$), the July
wage raise, the drawn random events, the recording layer, the refund stream —
all exactly as published. What is *new* is only bookkeeping that consumes no
randomness: the RE ledger silently accumulates toward its January-2026
formalization, and the cost sheet's new columns hold zeros.

## 7 Year two — 2026, "Growth, with scares"

| When | $t$ | Event | Mechanism | Intended reading |
|---|---|---|---|---|
| Jan 1 | 366 | **Books formalize** | RE opens at year-one surplus; owner draw begins ($\rho_{RE}=0.5$); year-one profit tax paid in cash; utilities tariff +6% | Q1 cash noticeably tighter than the naive reader expects |
| Feb 8 | 404 | **Freezer failure** | overnight compressor death: 100% of Frozen Foods stock and 30% of Dairy and Eggs written off at opening (`write_offs.reason = "damage"`); €1,800 emergency repair (cash + RE debit); frozen shelf capacity ×0.5 for 21 days (order cap) | a sharp, narrated inventory anomaly; delays the expansion; tests event detection vs. the answer key |
| Apr–May | 470–530 | **Avian flu** | scripted cost event on Dairy and Eggs: +18% invoice peak, 14-day ramp, 8-week decay (the P2 event machinery, scripted rather than drawn) | a second pass-through episode, single-category, cleanly identified |
| Jul 1 | 547 | **Wage raise** | +4% statutory | opex step |
| Jul–Aug | 547–608 | **Heatwave** | +3.5 °C temperature anomaly, Jul–Aug, ramping in and out over ~10 days (audit amendment: heat builds and breaks over days, never at midnight) | ice-cream boom *and* spoilage pressure (κ_T channel) — revenue and waste rise together |
| Sep–Oct | 609–650 | **The apartment block fills** | scripted arrival surge: ~9 new regulars phased over 6 weeks (fresh profiles, newcomer persistence mix); guest intensity +5% permanently | the growth the owner has been waiting for — realized, visible, and just before his capital crosses the line |
| ~Nov 1 | ~670 | **EXPANSION** (endogenous) | RE crosses $K_{exp}$ → the first clerk (8-hour shift), hours 07–21, shelf ×1.2, capex €14,000 | the owner's bet, placed at the exact peak of his world |

Random Phase 2 events keep firing throughout (rate 1.5/yr, fresh keyed draws)
— the script is the melody, not the whole soundtrack.

## 8 Year three — 2027, "The squeeze"

| When | $t$ | Event | Mechanism | Intended reading |
|---|---|---|---|---|
| Jan 1 | 731 | **Rent renewal +12%**; utilities +3%; year-two profit tax paid | contract schedule (§5) | fixed costs step up exactly when revenue is about to step down |
| Mar 1 | 790 | **A discounter opens 600 m away** | permanent visit-probability penalty ramping in over 4 weeks, **heterogeneous by customer**: $m_i = \exp(-\chi \cdot \tilde{s}_i \cdot k_i)$ with $\tilde{s}_i$ the customer's price-sensitivity percentile and $k_i = 1.0$ for transients, $0.6$ for rooted (relationships hold people); $\chi$ calibrated to an aggregate −9% visit rate; guests ×0.85 | the price-hunters defect first. Observed premium share and average basket *rise* after entry — a pure composition effect masquerading as up-trading (lesson #12) |
| May 1 | 851 | **The owner fights back** | markup −4 pts on the three price-visible categories (Beverages (Non-Alcoholic), Snacks and Confectionery, Household and Cleaning Supplies); promo trigger loosened 4→3 weeks | margin squeeze in the cost sheet; and a textbook endogeneity trap — promos intensify *after* revenue falls, so naive promo-lift estimates in 2027 are contaminated (lesson #14) |
| Aug 7–20 | 950–963 | **Street festival** relocated to the store's street | guests ×2.3 for 14 days; festival baskets small and cash-heavy | one good fortnight; tests one-off event attribution against the answer key |
| Sep–Nov | 994–1064 | **Commodity spike** | scripted cost event on Pantry Staples and Packaged Goods + Bakery and Bread: +14% peak, 10-week decay | the third pass-through episode — same mechanics, different competitive regime; comparing the three episodes *is* the analysis |
| Dec 31 | 1095 | **The books close** | — | after-tax result thin; the capstone question: renew the lease for 2028–29, or close? Three years of believed/realized/oracle triptychs and the twin arms grade the answer |

**On the discounter's mechanism.** The penalty enters each affected customer's
visit probability exactly where `traffic_mult` would, but per-identity — the
outside option got better, and it got better *more* for people who care about
price. Category demand, basket composition, and the "premium drift" all follow
from who stopped coming, not from any scripted preference change. The
`no_competitor` twin (§9) is the ground truth for every entry-impact estimate.

## 9 Counterfactual arms (the graded twins)

The Phase 4 laboratory extends to the new script. Two arms become first-class
reference scenarios, CRN-locked to the three-year baseline:

| Arm | Spec | Grades | Measured twin-diff |
|---|---|---|---|
| `3y_no_competitor` | year-three entry deleted (χ = 0, guests unchanged); owner's May response consequently never triggers (it is keyed to the entry script, not to revenue) | the true cost of entry; the contamination of 2027 promo estimates | 2027 revenue €823k without entry vs €807k with; three-year realized €88k vs €83k — the discounter costs ~€5k net of the response |
| `3y_no_expansion` | `expansion_threshold = None`; hours, staff, shelf stay at year-one values | the expansion's true NPV — was the owner's bet right? | three-year realized €165k vs €83k — the bet costs ~€82k, an order of magnitude more than the discounter |

The five existing year-one scenario arms stay exactly as published — their
one-year horizon is part of their identity, and regenerating them on the
three-year horizon would change files without changing meaning
(implementation amendment to the first draft). Full `--all-scenarios`
runtime roughly triples (~11 min); acceptable.

## 10 Planted lessons (new, continuing the numbering)

| # | Lesson | Where it hides | Graded against |
|---|---|---|---|
| 11 | **Survivorship bias**: tokens that vanish are churn, not lapse; panels of always-present customers overstate loyalty and stability | visible receipts (silence is the only signal) | hidden `arrival_date` / `departure_date` |
| 12 | **Composition vs. behavior**: post-entry premium-share and basket rise with zero up-trading — the mix changed, not the people | 2027 receipts | hidden `persistence` + who departed |
| 13 | **Investment at the peak**: the expansion is ex-ante sound under the censored forecast and ex-post ambiguous once the discounter lands | cost sheet + 2027 revenue | `no_expansion` twin |
| 14 | **Endogenous response**: price cuts and promos intensify *after* revenue falls; 2027 promo-lift estimates are confounded by the response being caused by the decline | promotions log + price history | `no_competitor` twin |
| 15 | **Trend–seasonality identification**: one year cannot separate them; three can | monthly aggregates | scripted $M_{ct}$ + panel-growth script |
| 16 | **Forecast under regime change**: a model trained on 2025–26 breaks in March 2027 and never learns why | any forecasting exercise | holdout year + twins |
| 17 | **Contracts are lumpy**: rent steps, wage steps, tariff steps — cost "inflation" is not a smooth index, and Q1 cash bears the tax bill | cost sheet | the §5 schedule |

## 11 Interface contract (what changes where)

- **params.py** — `PHASE2["n_days"]` 365 → 1095; new `PHASE5` dict (§12);
  `K_PANEL = 10` in keys.py.
- **phase2.py** — calendar, weather, paths extend to $t = 1095$ (weather
  seasonality is day-of-year indexed and extends naturally; multiplier
  normalization runs over the full horizon so the *panel*, not $M_{ct}$,
  carries the trend). Rates gain the wage-raise list and tariff schedule;
  budgets become $(N, 156)$ with the spell machinery unchanged.
- **world.py** — panel flow state (active mask per month, arrival/departure
  ledger); rent schedule; time-varying `hired(t)`, `open_hour(t)`,
  `close_hour(t)`, shelf capacity.
- **phase3.py** — monthly close gains: churn/arrival resolution, owner draw,
  RE ledger, expansion trigger + capex, January profit-tax payment. The daily
  loop reads staffing/hours/shelf per day. Freezer, discounter penalty,
  festival, and response enter as scripted hooks with the same shape as
  Phase 4's (they are baseline script now, not scenario arms).
- **recording.py** — runs per calendar-year block, keyed by year (§2).
- **export.py** — cost sheet new columns + calendar months; three
  `tax_statement` rows-per-year; hidden `customers.csv` gains
  arrival/departure/persistence; new hidden `panel_ledger.csv` if needed for
  grading (arrivals, departures, causes).
- **validate.py** — all band-calibrated checks re-scoped per year; new:
  **(31)** the exogenous script's year-one byte-identity vs. the one-year
  baseline; **(32)** panel
  accounting identity ($N_t = N_0 + \text{arrivals} - \text{departures}$,
  ledger vs. data); **(33)** RE ledger reconciles to the cash identity to the
  cent; **(34)** the expansion fires exactly once, in autumn 2026; **(35)**
  the discounter arm's twin-diff is negative, concentrated in
  transient/price-sensitive customers, and guests drop ~15%.
- **Workbook** — out of scope for Phase 5 proper; the retrofit (year
  dimension everywhere, `DATE '2025-01-01'` unhardcoded, month aggregations
  grouped by year) is its own task after the data exists. KPI references
  become a new vintage by definition.

## 12 Parameters

```python
PHASE5 = {
    "horizon_years": 3,                      # 2025-01-01 .. 2027-12-31
    # (plus the 2026/2027 holiday, major-holiday, and closure calendars)
    "panel": {
        "transient_share": 0.20,             # §3: come-and-go residents
        "transient_monthly_hazard": 1 / 18,  # mean tenure 18 months
        "newcomer_transient_share": 0.50,    # movers are likelier to move again
        "replacement_delay_p": 0.50,         # 1 + Geometric(p) months to refill
        "growth_trickle_per_year": 4,        # Poisson mean, net new households
        "churn_start_month": 1,              # the panel flows from day one (§2)
        "apartment_block": {
            "t_from": 609,                   # 2026-09-01
            "n_new": 9,
            "ramp_days": 42,
            "guest_mult": 1.05,              # permanent
        },
    },
    "finance": {
        "formalize_month": 13,               # RE ledger + owner draw begin
        "retain_ratio": 0.50,                # rho_RE
        "expansion_threshold": 52_000.0,     # K_exp; calibrated -> autumn 2026
        "expansion_capex": 14_000.0,
        "expansion": {
            "hired_extra": 1,
            "clerk_hours_per_day": 8,        # part-time shift (amendment, §4.2)
            "open_hour": 7,
            "close_hour": 21,
            "shelf_mult": 1.2,
        },
        # January pays the prior year's profit tax in cash — the P4 accrual
        # idealization ends with the formalized books (§4.1)
    },
    "contracts": {
        "rent_mult_from_t": (731, 1.12),     # 2-yr contract renews 2027-01: +12%
        "wage_raises": [                     # 2025-07's +4% stays in PHASE2
            (547, 0.04),                     # 2026-07
            (912, 0.05),                     # 2027-07
        ],
        "utility_tariff": [
            (366, 1.06),                     # 2026-01 reset
            (731, 1.03),                     # 2027-01 reset
        ],
    },
    # the year-two and year-three script events live as TOP-LEVEL keys, so a
    # twin arm can switch a single mechanism off with one shallow override
    # (e.g. "competitor": None) — implementation amendment
    "freezer": {
        "t": 404,                            # 2026-02-08
        "frozen_loss": 1.00,
        "dairy_loss": 0.30,
        "repair_cost": 1_800.0,
        "frozen_cap_mult": 0.5,
        "cap_days": 21,
    },
    "avian_flu": {                           # rides the P2 event machinery
        "type": "avian_flu",
        "start": 470,
        "ramp": 14,
        "decay": 56,
        "cats": {
            "Dairy and Eggs": 0.18,
        },
        "utility_peak": 0.0,
    },
    "heatwave": {
        "t_from": 547,
        "t_to": 608,
        "temp_delta": 3.5,
        "ramp_days": 10,                     # no square edges (audit amendment)
    },
    "competitor": {
        "t": 790,                            # 2027-03-01
        "ramp_days": 28,
        "target_visit_drop": 0.09,           # calibrates chi
        "rooted_factor": 0.6,
        "guest_mult": 0.85,
    },
    "response": {
        "t": 851,                            # 2027-05-01
        "markup_cut": 0.04,
        "cut_cats": [
            "Beverages (Non-Alcoholic)",
            "Snacks and Confectionery",
            "Household and Cleaning Supplies",
        ],
        "promo_trigger_cover": 3.0,
    },
    "festival": {
        "t_from": 950,                       # 2027-08-07, two weeks
        "t_to": 963,
        "guest_mult": 2.3,
    },
    "commodity": {                           # rides the P2 event machinery
        "type": "commodity_spike_2027",
        "start": 994,
        "ramp": 14,
        "decay": 70,
        "cats": {
            "Pantry Staples and Packaged Goods": 0.14,
            "Bakery and Bread": 0.14,
        },
        "utility_peak": 0.0,
    },
}
```

## 13 Open questions, with proposed answers

1. **Should year-one churn exist?** *Settled: yes* (amended 2026-07-16). The
   first vintage started churn at month 13 to keep year one byte-identical to
   the published baseline — and the auditor pass flagged exactly the
   predicted tell (zero regulars going silent in 2025, then 15 and 36 in the
   later years). Realism won: churn, replacements, and the growth trickle now
   run from month one, and the identity contract narrowed to the exogenous
   script (§2).
2. **Does the owner re-run the assortment MILP at expansion?** *Proposed: no.*
   Expansion is depth (shelf ×1.2) and hours, not breadth; the
   fixed-assortment contract and its censoring-spiral evidence survive. An
   assortment refresh remains the deferred iteration-4 item it always was.
3. **Does the owner's May-2027 response depend on realized revenue
   (endogenous) or on the script (scheduled)?** *Proposed: scheduled,*
   keyed to the entry event. A truly endogenous trigger would fire in the
   `no_competitor` twin under some random paths and wreck the twin's
   interpretability. The lesson (#14) needs the response to *follow* the
   entry, which scheduling guarantees.
4. **Do transient departures cluster seasonally** (moving season)?
   *Proposed: not in this iteration* — constant hazard, one less confound in
   the survival-analysis lesson. Note as a realism refinement.
5. **Does the discounter affect guests' basket composition too?**
   *Proposed: no* — guests only lose arrival intensity (×0.85). Guests carry
   no price-sensitivity state, and inventing it now would touch Phase 1.

## 14 Implementation plan and validation checklist

Order of work (each step ends runnable, year-one hash checked) — **all steps
complete, 2026-07-16**:

1. Horizon plumbing: `n_days = 365·horizon_years`, calendar/weather/paths/
   budgets extend in **per-year keyed blocks** (the AR(1) chains and the rain
   Markov chain continue from the previous block's last state; every
   normalization runs per year-block) — year-one draws are stream-for-stream
   the baseline's.
2. Panel flow (`K_PANEL = 10`, monthly resolution, exports, checks P5-31/32).
3. Finance layer (draw, RE, January tax, cost-sheet columns, check P5-33/34).
4. Expansion trigger + time-varying staffing/hours/shelf; $K_{exp}$
   calibrated on the realized path (42k fired in spring → 52k lands Nov 1).
5. Year-two script (freezer, avian flu, heatwave, apartment block).
6. Year-three script (rent step, competitor χ calibration, response,
   festival, commodity; check P5-35).
7. Recording layer runs per calendar-year binder with per-year keys; the full
   30-check suite still passes on the regenerated one-year baseline, which
   stays **byte-identical to the published files** (verified via git); the
   three-year arms' year one shares the baseline's exogenous script but
   carries a live panel (§2 amendment).
8. Twins `3y_no_competitor` / `3y_no_expansion`; comparison.csv covers all
   nine arms.
9. Reference numbers recorded in ACCOUNTING.md; README status update.

The workbook retrofit (year dimension) follows as its own task once the data
is stable.

## 15 Measured reference numbers (seed 20260712, live-panel vintage of 2026-07-16)

`3y_baseline` (data/scenarios/3y_baseline/):

| Year | Revenue | Profit before tax | Tax | After tax | Notes |
|---|---|---|---|---|---|
| 2025 | 742,977 | 36,056.90 | 7,211.38 | 28,845.52 | the baseline's script with a live panel (§2): near, not equal to, the published one-year figures |
| 2026 | 771,317 | 49,940.82 | 9,988.16 | 39,952.65 | growth year; expansion Nov 1 (capex €14k, RE €40.9k after) |
| 2027 | 814,278 | **−481.35** | 0 | −481.35 | the squeeze: rent +12%, a full year of the clerk, the discounter — a knife-edge year |

Panel: 259 opening regulars → 321 ever-present identities over three years
(replacement churn from month one + trickle + the block); regulars go silent
in every year (10 / 12 / 23 by last-purchase year). χ calibration: transient
defection ×0.87 vs rooted ×0.92, aggregate ×0.910. Twins: `3y_no_competitor`
realized €91.3k / oracle €101.3k; `3y_no_expansion` realized €167.2k /
oracle €192.6k; `3y_baseline` realized €85.5k — the expansion (~€82k + €14k
capex) dwarfs the discounter (~€5.8k), and only the twins can prove it.
Recording layer: the all-even dedup rule has **two natural false positives**
in three years (single-line double-scanned baskets; residues −€4.89 in 2025
and −€13.40 in 2026, each traceable to one receipt) — the structural blind
spot the reconciliation contract documents (ACCOUNTING §9).
