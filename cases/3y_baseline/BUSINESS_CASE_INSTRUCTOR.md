---
arm: 3y_baseline
data: data/scenarios/3y_baseline/
twins:
  - 3y_no_competitor
  - 3y_no_expansion
brief: BUSINESS_CASE.md
---

# Malm's Market — Instructor Appendix

*(Companion to `BUSINESS_CASE.md`. Never distributed with the brief. See
`documents/CASE_WRITING_GUIDE.md` for the rules this appendix implements.)*

## 1 The question map

Each brief question, its catalog rows (`ANALYSIS_CATALOG.md`), the grading
source, and what a full-credit answer contains.

| # | Henrik's question | Catalog | Graded against | Full credit requires |
|---|---|---|---|---|
| 1 | "Show me where the money goes" | Layer 1 (1.1, 1.8) after Layer 0 | ledger identities; `imperfections.csv` for the cleaning that precedes it | a reconciled P&L (till tied to ledger per year), the margin waterfall, and the per-year arc +36k / +50k / −0.5k stated plainly |
| 2 | "Am I really growing?" | 7.1, 1.3 | `demand_modifiers.csv` (mean-one per year ⇒ trend ≠ season), `customers.csv` arrivals | trend separated from seasonality with 3 annual cycles; growth attributed to panel + prices + hours, not to season; the January-2025 cold-start excluded from "growth" |
| 3 | "Shrinkage — theft?" | 0.5, 0.3, 0.4 | `imperfections.csv` | the decomposition: spoilage vs. count corrections vs. the freezer; spike months traced to double-posted invoices; the explicit verdict **no theft signal** |
| 4 | "What did Spara+ cost me?" | 7.3, 7.5 | `3y_no_competitor` twin | refusal of the naive before/after (the entry is invisible against growth); a constructed counterfactual (forecast- or twin-based); an estimate near −€17k revenue / ≈−€6k profit for 2027; explicit correction of Henrik's framing |
| 5 | "Was the expansion worth it?" | 7.9 | `3y_no_expansion` twin | the bet priced (≈ −€82k operating over 14 months + €14k fit-out); the mechanism named (fixed wage vs. 18% margin; deeper shelves partly rotting); ex-ante fairness acknowledged |
| 6 | "Which customers am I losing?" | 7.2 | `customers.csv` arrival/departure/persistence | churn read from token silence with the right-censoring caveat; the flow framing (departures ≈ replacements + slow growth + the block cohort); survivorship warning on any loyalty metric |
| 7 | "What will 2028 look like?" | 3.1, 7.5 | holdout logic; the twins for regime honesty | a range, not a point; explicit conditioning ("if the expansion stays / goes"); seasonal-naive benchmark beaten or honestly tied |
| 8 | "Renew, close, or change?" | 7.11, 4.6 | both twins together | the decomposition of 2027 (expansion ≫ competitor ≫ contracts); the recommendation **renew the lease, reverse or restructure the expansion**; the lease framed as the wrong lever |

## 2 The wrong belief (the case's spine)

Henrik attributes 2027 to Spara+ and is contemplating *not renewing* — the
one decision the numbers do not support. Truth (twin-graded): the entry
cost ≈ €6k of 2027 profit; his expansion cost roughly ten times more over
its lifetime. Full credit on Q4/Q5/Q8 requires **explicitly telling the
client he is wrong**, with evidence, while acknowledging what he got right
(the leak is real, his May price cuts did contain it).

## 3 The trap list

| Trap | Where it bites | The tell | Resolution |
|---|---|---|---|
| January 2025 cold-start | Q2, any seasonality read | slow-replenishing categories (incl. the "flat" cleaning aisle) glow in month 1 | the opening stock-up, per the interview ("filling pantries, not shopping normally"); exclude or model month 1 |
| Schedule composition | Layer 1 rhythms | Saturday/Sunday peaks | shopper *composition*, not day preference — primary-day habits |
| "Theft" | Q3 | big count corrections in scattered months | each spike traces to one invoice keyed twice; Henrik's confession points here |
| The invisible entry | Q4 | no break in any top-line series at March 2027 | growth + extended hours mask the leak; only a counterfactual reveals it |
| The silent markdown machine | any promo analysis | all 11 campaigns sit in 2025 | overstock-triggered promos stopped firing once demand grew; there is nothing after 2025 to evaluate — and the May 2027 cuts are a *response*, endogenous to the entry |
| The dedup blind spot | Layer 0 | two years leave small tie residues (−€4.89, −€13.40) | naturally all-even receipts (single-line double-scans); locatable from the residue amounts alone |
| Hour-comparison drift | Q2, Q7 | 7h/20h cells exist only after Nov 2026 | the opening-hours change; compare like hours only |
| Right-censored churn | Q6 | recent quiet tokens | silence ≠ departure near the window's edge; use a conservative cutoff |

## 4 Reveal staging

1. **Stage A (hand out):** `BUSINESS_CASE.md` + the arm's `visible/` +
   `SKUs.xlsx`. Nothing else.
2. **Stage B (after submission):** the graded notebooks —
   `clean_and_describe.py`, `three_year_review.py`,
   `competitor_entry_study.py`, `expansion_review.py` — as the worked
   solution narrative.
3. **Stage C (debrief):** `hidden/` (answer keys) and the twin arms
   (`3y_no_competitor/`, `3y_no_expansion/`), which turn Q4/Q5/Q8 from
   argued answers into measured ones.

Never bundle Stage C with Stage A; the twins trivially answer the two
hardest questions.

## 5 Rubric hooks (binary checks per question)

- **Q1**: tied till to ledger per year before charting? stated the arc in
  the client's terms?
- **Q2**: excluded/handled month 1? separated trend from season with an
  actual method (overlay, decomposition, or regression), not a claim?
- **Q3**: split write-offs by reason? traced at least one spike month to
  its duplicated invoice? said "no theft" explicitly?
- **Q4**: rejected before/after explicitly? built any counterfactual?
  landed within a factor of ~2 of −€17k revenue? corrected the client?
- **Q5**: priced the bet including the fit-out? named the wage-vs-margin
  mechanism? avoided hindsight moralizing (ex-ante reasonableness noted)?
- **Q6**: handled right-censoring? described churn as a flow with
  replacement, not just attrition?
- **Q7**: gave a range with stated assumptions? benchmarked against
  seasonal-naive?
- **Q8**: decomposed 2027 across the three causes? recommendation targets
  the payroll/expansion, not the lease? deadline-ready (one page the
  client can act on)?

## 6 Vintage note

The brief's pinned facts (dates, rents, the repair bill, hours, the
closure days) are stable per seed. Emergent details (which months' count
corrections spike, the exact residue amounts) can move if the data is
regenerated — re-run the case QA sweep (`CASE_WRITING_GUIDE.md` §5) after
any regeneration, and update §3's residue amounts here if they change.
