# Phase 4 — The Policy Laboratory: Scenarios and the Tax Layer

*(2026-07-14. Builds on Phases 1–3; consumes their interfaces and changes none of them.)*

Phases 1–3 produced one performed year. Phase 4 makes the year *re-performable
under different macro conditions*: a scenario is a set of edits to the exogenous
script and the owner's policy knobs, replayed through the identical keyed-RNG
market loop, so that every difference between two arms is causally attributable
to the scenario by construction (the CRN discipline of P2 §13 / P3 §12, promoted
from the oracle's private trick to a public instrument). The tax layer is what
makes the laboratory *economic*: taxes are the lever through which macro policy
reaches microeconomic agents, and each of the three textbook channels lands on a
mechanism the simulation already has.

**The governing principle: agents never see "the policy."** Customers see prices
and budgets; the owner sees invoices, tags, wages, and his till. A VAT reform
enters the world as a change in gross invoice costs and remittances — nothing
else — and everything downstream (pass-through, substitution, demand) *emerges*
from Phase 1–3 behavior rather than being scripted.

---

## 1 The folder contract

The baseline is one arm among the scenarios — same structure, no privileged
location (2026-07-15 amendment):

```
data/scenarios/<name>/visible      <- one arm's analyst dataset
data/scenarios/<name>/hidden       <- its answer key
data/scenarios/baseline/           <- the reference year, an arm like any other
data/scenarios/comparison.csv      <- one row per generated arm
```

Every scenario arm passes through the same recording layer (P3 §20) and the
same export, so scenario data is exactly as dirty, and exactly as cleanable, as
the baseline.

## 2 The tax layer (baseline, not scenario-only)

Taxes exist in the *baseline* world — a tax-free shop was itself a realism gap —
and scenarios vary the rates. Three instruments:

**VAT, differential by category.** All prices in the world are and always were
*gross*: the catalog's retail prices, the supplier invoices, the shelf tags.
The tax layer makes the embedded VAT explicit. Categories split into a reduced
group (food, at $r^{red} = 10\%$) and a standard group (Alcoholic Beverages,
Household and Cleaning Supplies, Personal Care and Health, at $r^{std} = 20\%$).
Each category carries a *rate path* $r_c(t)$; the baseline paths are constant.

- **Price formation is tax-aware the way a real shopkeeper's is** (2026-07-15
  amendment). The owner knows the VAT is not his money: the cost trend he
  tracks is the **net** (tax-exclusive) invoice EWMA, his markup applies to
  that, and the day's rate is re-applied on top —
  $\text{tag} = \text{charm}\big(\overline{\text{NetCost}} \cdot (1 + m_c) \cdot (1 + r_c(t))\big)$.
  At constant rates this is algebraically identical to marking up the gross
  invoice; when a rate changes, the new rate reaches his *target* price
  immediately and exactly. Pass-through to actual shelf tags is still
  **incomplete, delayed, and charm-quantized** — but now purely because of the
  menu-cost hysteresis and the reprice-on-delivery cadence, which is exactly
  the friction the empirical VAT-pass-through literature identifies. A scenario
  rate change still enters the world as the gross-invoice factor
  $(1 + r_c(t)) / (1 + r_c(0))$ riding the cost-path channel.
- **Remittance is real cash.** Monthly, the ledger accrues output VAT
  $\sum \text{sales}_c \cdot \frac{r_c}{1+r_c}$ minus input VAT
  $\sum \text{purchases}_c \cdot \frac{r_c}{1+r_c}$, and the net leaves the till
  at the close — the till that funds the cash-capped ordering rule (P3 §8).
  Refund lines net out of output VAT automatically.

**Payroll tax.** Employer contributions at $r^{pay} = 25\%$ on gross wages, a
separate ledger column. Zero at the baseline (the owner works alone, unpaid) —
it exists so that *hiring* scenarios carry the true cost of labor.

**Profit tax.** A small-business flat rate $r^{\pi} = 20\%$ on positive realized
annual profit, **accrued, not cash-moved** (it is paid the following January,
after the records close). It appears in the annual `tax_statement` and extends
the triptych: believed / realized / oracle now each close to an after-tax line.

**The owner and taxes — aware, not strategic** (2026-07-15 amendment). Three
behaviors make him as tax-aware as any real shopkeeper: he prices on *net*
margin (above); he costs hiring at the **full employer price** — wage plus
payroll contributions — in the opening MILP; and he keeps a **tax jar**: the
profit tax accruing on the year-to-date result is set aside mentally and never
counts as ordering headroom, even though the cash only leaves in January. What
he deliberately does *not* do is tax-*strategic* optimization: no cross-category
margin rebalancing when rates diverge, no elasticity-aware pass-through of a
hike, no tax-timing games. For a flat profit tax this is provably harmless
(maximizing $(1-\tau)\pi$ picks the same actions as maximizing $\pi$); for VAT
it is the analyst's open door — the gap between his mechanical rule and a
demand-aware repricing is measurable against the twin arms. One consequence of
the payroll amendment accepted in review: the MILP's labor coefficient changed,
so CBC returned a different vertex of the (heavily degenerate) opening
assortment within the optimality gap — same location, same believed profit, a
reshuffled SKU list — and the baseline regenerated as a new vintage.

**New artifacts.** `cost_sheet.csv` gains `vat` (net remittance) and
`payroll_tax` columns; a new visible `tax_statement.csv` summarizes the year
(output VAT, input VAT, remitted, payroll tax, profit before tax, profit tax,
profit after tax); `profit_triptych.csv` gains the after-tax fields.

## 3 The scenario specification

A scenario is a declarative spec; every field edits the *script* or a *policy
knob*, never an RNG key:

| Field | Edits | Mechanism it rides |
| --- | --- | --- |
| `events_add` | extra Phase-2 cost events | `gen_paths` trajectories -> invoice costs -> repricing |
| `weather_edit` | scripted day ranges (temp delta, rain, wet) | applied before `gen_paths`, so demand modifiers and spoilage factors feel the storm |
| `traffic_mult` | day-range multipliers on traffic $\Lambda_t$ | visits |
| `budget_mult` | week-range multipliers on $B_{iw}$ | income effects, the tight-spell machinery's mirror image |
| `vat_schedule` | rate-path changes $r_c(t)$ from a date | invoice gross factor + remittance |
| `policy` | `hired_extra`, `open_hour`, `close_hour` | wages (+ payroll tax) and the arrival-hour gate |

The staffing knob is honest by construction: one owner cannot run more than a
12-hour day, so extended hours *require* the hire; the extra hours convert part
of the `closed`-cause hidden demand (P3 §5 already ledgers every out-of-hours
arrival) into sales, and the question the scenario answers is whether that
recovered demand pays the gross wage bill.

## 4 The reference scenarios

| Name | Story | Spec essence | Expected fingerprint |
| --- | --- | --- | --- |
| `war_june` | a broad supply shock from June 1 | ALL-category cost event, log-peak 0.30, ramp 14 d, decay 120 d | all cost paths spike; tags follow with hysteresis; outside option and `budget` losses grow |
| `typhoon_september` | a 3-day storm, Sep 8–10 | rain 60 mm, temp −5 °C, wet; traffic ×0.35 those days; short sharp cost event on Fresh Produce & Seafood | storm-day footfall collapses; substitution away from the shocked categories |
| `food_vat_cut_july` | reduced VAT 10% -> 5% from Jul 1 | `vat_schedule` on the reduced group | food invoice costs drop ~4.5%; tags follow *incompletely* (hysteresis); H2 remittance falls |
| `tax_rebate_spring` | a transfer to households, weeks 14–17 | `budget_mult` ×1.20 | baskets lengthen; `budget`-cause hidden demand thins; April revenue jumps |
| `second_clerk` | hire one clerk, open 7:00–22:00 | `hired_extra = 1`, hours 7–22 | sales appear outside 8–20; wages + payroll tax nonzero; `closed` ledger shrinks |

One honest limitation, stated rather than hidden: a *temporary* rebate does not
shift customers toward premium brands, because brand affinity is a fixed trait
(income-correlated cross-sectionally via P1 §3, but not responsive to a
windfall). Windfall uptrading would need a budget-slack term in the brand
utility — deferred until an analysis layer wants to measure it.

## 5 Validation

The baseline keeps its full suite (now 29+ checks), extended with: the VAT
remitted equals the rate map applied to actual sales and purchases (recomputed
independently); profit after tax < profit before tax; payroll tax = 0 while the
owner works alone. Scenario arms run a *structural* subset — conservation,
closure days, refund integrity, receipts-to-ledger tie — because the
realism-band checks are baseline-calibrated (a war year *should* fail the
Fri–Sun band); each reference scenario additionally asserts its own fingerprint
from the table above.

## 6 Parameters

```python
PHASE4 = {
    "vat_reduced": 0.10,
    "vat_standard": 0.20,
    "vat_standard_categories": [
        "Alcoholic Beverages",
        "Household and Cleaning Supplies",
        "Personal Care and Health",
    ],
    "payroll_rate": 0.25,
    "profit_tax_rate": 0.20,
}
```

Scenario specs live in `datagen/scenarios.py`; the entry point grows
`--scenario <name>` (repeatable) and `--all-scenarios`, writing the comparison
file whenever more than one arm is generated. Consequence accepted in review:
introducing real VAT remittance changes the baseline's cash path, so the
baseline regenerates as a new vintage; all reference numbers in
`documents/ACCOUNTING.md` are re-measured.
