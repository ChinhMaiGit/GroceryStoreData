# Accounting Processes — How Every Euro and Every Unit Moves

This document describes the complete accounting model of the generated grocery-store
world: where money and goods originate, which artifact records each movement, the
exact identities that hold between artifacts, and the deliberate imperfections that
make the raw files disagree until they are cleaned. It is written for an analyst
working from `data/visible/`; pointers to the design rationale reference the
phase documents (`documents/PHASE1..3_DETAILS.md`, abbreviated P1/P2/P3 below).

Parameter values quoted here come from `datagen/params.py` (`PHASE1`, `PHASE3`,
`PHASE4`, `IMPERFECTIONS`). Euro amounts marked *(reference year)* are measurements
of the currently shipped dataset, not parameters.

---

## 1 The chart of artifacts

| File (`data/visible/`) | What it records | Grain |
|---|---|---|
| `receipts.csv` | every till transaction: sales, voided mis-rings, refunds | line item |
| `price_history.csv` | every shelf-tag change | SKU × change date |
| `promotions.csv` | markdown campaigns and their flyer cost | campaign |
| `procurement.csv` | supplier invoice lines | order line |
| `inventory_eod.csv` | end-of-day **book** stock | SKU × day |
| `write_offs.csv` | logged spoilage + monthly stock-count corrections | SKU × day |
| `cost_sheet.csv` | the owner's monthly ledger (authoritative for money) | month |
| `tax_statement.csv` | the annual tax filing: VAT remitted, payroll tax, profit tax accrual | year |
| `calendar.csv`, `weather.csv`, `locations.csv` | context | day / site |

Scenario arms (P4) replicate this exact structure under
`data/scenarios/<name>/`, with `data/scenarios/comparison.csv` summarizing all
generated arms; everything below applies to every arm identically.

One principle governs everything: **the ledger (`cost_sheet.csv`) is the owner's own
accounting and is always right about money.** The transaction files are the raw
paperwork; they contain recording defects (Section 8) and only reconcile to the
ledger after cleaning.

---

## 2 Opening the business (one-time capital movements)

The owner starts with **€40,000 capital** (`PHASE1["capital"]`). Before day 1, the
opening plan (P1's MILP) spends, one time only:

- **Setup cost** of the chosen location (`locations.csv → setup_cost`);
- **Listing fees**: €2.50 per stocked SKU (`listing_fee`), 128 SKUs;
- **Initial stock**: the opening quantities `q0` bought at base cost.

The MILP also *budgeted* month-1 rent, wages, and utilities, but the ledger charges
those at the monthly close instead, so that budget is returned to opening cash (see
the `cash = ...` initialisation in `run_year`). These one-time outlays never appear
in `cost_sheet.csv` — they are charged directly against annual profit (Section 7).

---

## 3 Revenue: the till

### 3.1 Ordinary sales

Every purchase line posts `qty × unit_price` to the month's revenue **and to cash on
the same day** — the till is cash-basis and immediate. `unit_price` is the
*effective* price actually paid, produced by this waterfall:

1. **Shelf price** — `(1 + markup) × cost-EWMA`, snapped to the SKU's habitual
   charm ending (Section 4);
2. **Markdown** — if the SKU is in a live markdown campaign, the tag shows the
   discounted, re-charmed price instead;
3. **Loyalty Sunday** — on the last Sunday of each month, 5% off storewide is taken
   **at the till, not the tag** (`loyalty_depth`), so the paid price can undercut
   `price_history` on those days.

Lines sold under (2) or (3) carry `promo = 1`. For every `promo = 0` line, paid
price equals the posted tag exactly — that is a valid audit an analyst can run.

Payment is `card` or `cash`. Card transactions carry a stable hashed token in
`customer_id` (regular customers keep one token all year; one-off guests get
single-use tokens); cash lines have no identity.

### 3.2 Voided mis-rings (recording noise, no money)

~0.6% of receipts contain a **void pair**: the cashier scanned the wrong item and
cancelled it, leaving `+q` and `−q` lines of the same product at the same price
inside the same receipt. They net to **zero money and zero goods**. They are
distinguishable from refunds by having **no** `ref_receipt_id`.

### 3.3 Refunds (real money, no goods) — P3 §21

With probability 0.6% per receipt (`refund_receipt_rate`), one line comes back 1–13
days later (`refund_max_lag_days`): 1–2 units, refunded **at the price actually
paid** (promo price included). The refund posts as **its own till transaction**:

- a fresh `receipt_id`, negative `qty`, the original's payment method and customer
  token;
- `ref_receipt_id` pointing at the original receipt — every refund resolves to a
  real earlier sale (validated; 106 refunds, €542.08, in the reference year);
- **cash and monthly revenue decrease on the refund day**;
- the returned item is **destroyed, not restocked** — refunds never touch
  inventory. If the return date falls on a closure day, the customer comes back the
  next open day.

Accounting rule of thumb: *money views keep refunds netted in; trip/basket views
exclude `ref_receipt_id IS NOT NULL` rows* (returning a yogurt is not a shopping
visit).

---

## 4 The price book

- Each SKU has a **habitual price ending** fixed at listing time: `.x9` / `.x5` /
  `.x0` with probabilities 0.86 / 0.09 / 0.05 (`PRICE_ENDINGS`).
- The shelf tracks a **smoothed cost trend** — an EWMA of invoice costs
  (α = 0.35) — not each noisy invoice, and reprices only when the implied charm
  price drifts more than **3%** from the current tag (`reprice_threshold`): menu-cost
  hysteresis, giving a realistic median of ~3 tag changes per SKU per year.
- `price_history.csv` logs the initial tag (day 1) and every subsequent change.
  Markdown and loyalty discounts do **not** appear here — markdowns live in
  `promotions.csv`, loyalty Sundays only in the paid prices.

---

## 5 Procurement: order → cash → delivery → invoice

The owner restocks **weekly, ordering Monday, receiving Wednesday** (lead time 2
days, `lead_days`).

1. **Forecast**: per category, a trailing 4-week moving average of *own sales*
   (deliberately censored by past stockouts — P3's censoring-spiral lesson).
2. **Order-up-to target**: `(7 + lead)/7` weeks of forecast plus the owner's safety
   buffer, allocated across the category's SKUs by recent sales share with a
   +1-unit Laplace floor so no listed SKU is ever starved to death.
3. **Financing cap**: the order is scaled down if its bill exceeds
   `cash + €20,000 − credit drawn − tax reserve` — the till's cash plus the
   credit line's remaining room, minus the profit-tax accrual the owner sets
   aside (Section 7.3).
4. **Shelf cap**: scaled down again if projected post-delivery stock would exceed
   the store's physical shelf capacity.
5. **Cash timing**: the supplier is paid **at order time** — cash and the month's
   `procurement` accrual both move on the *order* date, two days before goods
   arrive. (`procurement.csv` shows both `order_date` and `delivery_date`.)
6. **Invoice cost**: base cost × the category's cost path (inflation, shocks — the
   October refrigeration shock lives here) × per-line lognormal invoice noise
   (sd 2.5%) — supplier invoices never move in perfect unison.

`posted_date` records when the paperwork was *entered*: one batch lag per delivery
(0 days w.p. 0.70, 1–2 d w.p. 0.25, 3–9 d w.p. 0.05) plus ~4% straggler lines 1–2
days later. Quantity effects on book stock are backdated to `delivery_date`, as
goods-receipt systems do.

---

## 6 Inventory accounting

`inventory_eod.csv` is **book stock** — what the owner's records imply, not a
nightly physical count. Its governing identity, checkable per SKU per day:

```
book(t) − book(t−1) = deliveries(t) − sales(t) − write_offs(t)
```

where each term comes from the *recorded documents* (raw files, including their
duplicates), with two carve-outs:

- **exclude refund lines** (`ref_receipt_id IS NOT NULL`) from sales — refunds move
  money only (Section 3.3);
- the identity **breaks on exactly two consecutive diffs** wherever a snapshot typo
  was keyed in (24 mistyped nights → 48 broken diffs, reference year).

### 6.1 Spoilage (`write_offs.csv`, `reason = 'spoilage'`)

Perishables thin **nightly** by a Binomial draw at the category's rate (weekly
rates converted to nightly; scaled by a weather/energy-crisis factor). Write-offs
are logged **in units, at no explicit cost** — the euro cost of waste is implicit
in procurement (goods bought that were never sold). The workbook prices waste at
each SKU's median invoice cost when it needs euros.

### 6.2 Stock counts and shrinkage (`reason = 'stock_count'`)

On the **last day of each month** the owner counts the shelf and posts one
correction row per SKU whose books drifted: positive units = loss (shrinkage),
negative = count gain. The drift itself is produced by the recording layer's
document defects (unlogged tosses, duplicate/missing invoices, duplicated
receipts — Section 8), so the corrections are *explained* by defects an analyst can
independently find. Between counts, book stock can print **negative** — normal in
book inventory, impossible on a real shelf.

Analysts must keep the two `reason` classes apart: spoilage rows measure waste;
stock-count rows measure bookkeeping drift. Mixing them double-counts.

---

## 7 The monthly ledger and annual profit

### 7.1 `cost_sheet.csv` — one row per month, written at the monthly close

| Column | Definition |
|---|---|
| `revenue` | Σ till lines that month, **net of refunds** |
| `procurement` | Σ invoice bills for orders *placed* that month (cash-basis, order date) |
| `rent` | fixed monthly rent of the chosen location |
| `wages` | hired staff × hourly wage × opening hours × days in month. Wage rate rises 4% from July 1. **The owner is unpaid** — this store needs one person, who is the owner, so wages are €0 and every "profit" figure is really the owner's own compensation |
| `payroll_tax` | employer contributions at 25% of gross wages — €0 while the owner works alone, real money in staffing scenarios |
| `utilities` | hourly utility rate × opening hours × days; the rate carries inflation **and the Q4 energy-crisis spike** |
| `storage` | end-of-month on-hand units × unit storage rate (€0.02 × inflation) |
| `flyers` | €80 per markdown campaign triggered that month |
| `vat` | net VAT remittance: VAT collected on sales minus VAT paid on invoices, at each category's rate (Section 7.3) — leaves the till at the close |
| `credit_interest` | credit balance × 8% APR / 12 |
| `credit_balance` | credit drawn after the month's sweep |
| `cash` | till cash at month end, after the sweep |

**The credit-line sweep**, at every close: if cash is negative after charges, the
shortfall is drawn on credit and cash is set to zero; if cash is positive while
credit is outstanding, the line is repaid as far as cash allows. The €20,000 limit
binds *upstream*, in the ordering rule (Section 5, step 3): the owner never places
an order his cash plus remaining credit room cannot cover, so the sweep itself
never needs to enforce the cap.

### 7.2 Annual realized profit

```
profit before tax = Σ revenue
       − Σ (procurement + rent + wages + payroll_tax + utilities
             + storage + flyers + vat + credit_interest)
       − setup cost − listing fees − initial stock          ← the one-time openings
profit tax        = 20% × max(0, profit before tax)          ← accrued, paid next January
profit after tax  = profit before tax − profit tax
```

*(reference year: ≈ €36,479 before tax, €7,296 profit tax, €29,183 after tax;
the hidden answer key stores the believed / realized / oracle triptych with
after-tax lines.)*

### 7.3 The tax layer (P4 §2)

All prices in this world are **gross of VAT** — the shelf tags, the supplier
invoices, the catalog. Categories carry differential rates: 10% reduced (food)
and 20% standard (Alcoholic Beverages, Household & Cleaning, Personal Care),
each as a *rate path* that policy scenarios can change mid-year.

- **The owner prices on net margin.** He tracks the tax-exclusive invoice EWMA,
  applies his markup to that, and re-adds the day's rate on top — so a rate
  change reaches his *target* price immediately and exactly, while actual shelf
  tags still lag through the 3% repricing dead-band and charm quantization.
  The residual incomplete pass-through is pure menu-cost friction — measurable
  tax incidence, gradeable against the CRN-twin baseline.
- **Hiring is costed at the employer price** (wage × 1.25) in the opening MILP,
  and the owner keeps a **tax jar**: the profit-tax accrual on the year-to-date
  result is excluded from his order-financing headroom (Section 5, step 3).
- **Remittance**: monthly, `output VAT − input VAT` (rates applied to actual
  sales, net of refunds, and actual purchases) leaves the till — the same till
  that funds the cash-capped ordering rule.
- **Payroll tax**: 25% employer contributions on gross wages.
- **Profit tax**: 20% flat on the positive annual result, **accrued** in the
  `tax_statement`, not cash-moved in-year (it is paid the following January).
- Refund lines reduce output VAT at the rate in force on the *refund* day — a
  documented simplification (a mid-year rate change makes a handful of
  refunds remit at the new rate for old purchases).

---

## 8 The recording layer: why the raw files disagree (P3 §20)

The simulation is reality; the *documents* err. Injected at export, keyed by their
own RNG stream, each defect logged in `data/hidden/imperfections.csv`:

| Defect | Rate *(reference year)* | Accounting consequence |
|---|---|---|
| Duplicate receipt upload (POS retry, copies adjacent, same id, every line doubled) | 34 receipts | raw revenue overstated ~€1.5k until deduplicated |
| Void pairs | ~100 pairs | none — net zero by construction |
| Hour-0 clock glitch | 68 receipts | none on money; poisons time-of-day analysis |
| Payment label drift (`Card`, `CASH `, …) | ~1.2% of receipts | breaks naive GROUP BY payment |
| Duplicate invoice posting (always before its month-end count) | 22 lines | raw procurement overstated; feeds shrinkage |
| Missing invoice lines | 6 lines | invoices total **less** than ledger procurement — flag, don't fix; the ledger is right |
| Unlogged tosses | ~2.5% of write-offs | recorded spoilage *understates* true waste; surfaces as stock-count shrinkage |
| Snapshot typos | 24 nights | perpetual identity breaks in matched next-day pairs |
| Weather sensor outages | 6 days | NULLs; drop, don't impute |
| Promo category misspelling | 2 rows | silently un-joinable until normalized |

---

## 9 The reconciliation contract

What an analyst should expect each check to return, on the shipped data:

| Check | Expected result |
|---|---|
| Raw receipts Σ(qty × price) vs ledger revenue | **off by the duplicated uploads** (≈ €1.5k) |
| After retry-dedup (a receipt is a retry iff *every* distinct line's multiplicity is even → keep half) | **ties to the cent**, refunds already netted on both sides |
| Every refund's `ref_receipt_id` | resolves to a real earlier sale (0 orphans) |
| Invoice file after exact-line dedup vs ledger procurement | **short by the missing invoices** (a knowable € gap) |
| Perpetual-inventory identity per SKU-day, refund lines excluded | holds everywhere except 2-day typo pairs; monthly `stock_count` rows explain the shrinkage |
| Paid price vs posted tag on `promo = 0` lines | matches exactly |
| Paid price on `promo = 1` lines | markdown or loyalty-Sunday discount |
| Ledger `vat` column vs rates applied independently to receipts and invoices | ties within invoice-rounding cents (< €25/yr) |
| `tax_statement` arithmetic (remittance, payroll, profit tax) vs the ledger | closes exactly |

## 10 Known idealizations (documented, deliberate)

- No supplier dimension — invoices cannot be attributed to vendors (iteration 2).
- Deliveries land every Wednesday all year without holiday shifts.
- The assortment is fixed for the year (protects the censoring-spiral evidence, P3 §19.3).
- Procurement is cash-basis at order date; there are no payment terms or accounts payable.
- Refund fraud, partial-basket returns and restocked returns are not modeled; every
  refund is a destroy-on-return of 1–2 units of one line.
- The profit tax is accrued, not paid in-year. The owner is tax-*aware* in his
  accounting (net-margin pricing, employer-priced hiring, the tax jar) but never
  tax-*strategic*: no cross-category margin rebalancing when rates diverge, no
  elasticity-aware pass-through — the documented gap the prescriptive layer can price.
