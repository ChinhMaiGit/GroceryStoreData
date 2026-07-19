# Writing the Business Case — Instructions

*(2026-07-16. How to produce the client-facing case brief that accompanies a
dataset arm, and the instructor appendix that makes it teachable. Written for
the canonical `3y_baseline` first; §8 explains how the same instructions
generalize to any scenario arm, including future configurator-generated
ones.)*

A dataset without a business case is a pile of tables; the analyst can clean
it but cannot *recognize* it. The case supplies what the schema cannot: who
is asking, why now, what they already believe, and what a good answer would
change. These instructions exist so every case we produce does that job the
same way.

---

## 1 The two artifacts

Every cased arm ships two documents:

| Artifact | Audience | Contents | Location |
|---|---|---|---|
| **The brief** (`BUSINESS_CASE.md`) | the analyst/student | brand, persona, history, operations, data handover, the ask | `cases/<arm>/`, mirroring `data/scenarios/<arm>/`; frontmatter names the arm and data path |
| **The instructor appendix** (`BUSINESS_CASE_INSTRUCTOR.md`) | the instructor/grader | question-to-catalog mapping, planted traps, reveal staging, rubric hooks | same `cases/<arm>/` folder, never distributed with the brief; frontmatter also lists the grading twins |

The split is absolute: nothing in the brief may require the appendix to
parse, and nothing in the appendix may be needed to *attempt* the case.

## 2 The epistemic firewall (the one rule that outranks all others)

Three information sets exist in this project:

1. **The designer's** — mechanisms, parameters, modifiers, twins, answer
   keys (`hidden/`, the phase documents);
2. **The owner's** — what he lived through: events he witnessed, decisions
   he made, beliefs he formed (possibly wrong);
3. **The analyst's** — the owner's testimony plus `visible/`.

**The brief is written entirely inside information set 2.** Concretely:

- Every event mentioned must be something the owner could observe (a
  freezer died; a discounter opened) — never a mechanism (a demand
  modifier; a defection parameter χ).
- No number from `hidden/` may appear, and no number from `visible/` may
  appear *with more precision than an owner would carry in his head*
  ("about seven hundred forty thousand", never "742,977.31").
- Designer vocabulary is banned from the brief: *modifier, twin, CRN,
  planted, arm, scenario, oracle, censored*. If a sentence needs one of
  those words, it belongs in the appendix.
- The owner's beliefs need not be true (see §6) — but his *observations*
  must never contradict the data.

## 3 Element instructions

Work through these in order; each element states its job, what the data
pins, and what is free.

### 3.1 Brand & setting

**Job:** make the shop a *specific place* the analyst can picture, so that
data patterns land as recognition ("of course Saturday mornings — it's that
kind of shop") rather than as anonymous statistics.

- Invent: shop name, street, a **fictional town** (never a real one — real
  places import false facts), a one-line positioning statement.
- Pinned: a full-range neighborhood grocer (12 categories, ~128 products);
  euro prices; a holiday calendar with Easter, May Day, Midsummer, and
  Christmas closures (Central/Northern European texture); VAT at 10% food /
  20% non-food; a few hundred households in the catchment; one apartment
  building completed across the street in autumn 2026.
- The positioning must match the economics: this shop competes on
  *nearness and habit*, not price — the data shows premium and budget
  brands side by side, sticky charm prices, and an 18% gross margin.

### 3.2 Persona — the client

**Job:** every trait must be **load-bearing** — it must explain a pattern
the analyst will find. Decoration ("he likes fishing") is allowed only in
trace amounts; explanation is the point. Maintain this mapping when
drafting (and extend it if new quirks surface):

| Data pattern the analyst will hit | Trait that explains it |
|---|---|
| the monthly ledger is always right, to the cent | he does the books himself, every month-end, religiously |
| invoices duplicated / missing, receipt re-uploads | ...but paperwork bores him; the POS is old; entry happens in tired batches |
| deliveries every Wednesday, 156 weeks straight | a creature of habit; one supplier relationship he refuses to complicate |
| prices change only on delivery days, rarely | he reprices standing at the shelf with a label gun, only when the drift annoys him |
| wages = €0 for 22 months | he worked the floor alone, twelve hours a day |
| the tax jar, the retained-earnings discipline | prudent to a fault; the expansion waited until the money was *there* |
| the last-Sunday storewide discount | his one fixed marketing idea, kept since opening |

- Invent: name, age, family situation, the founding motivation (e.g.,
  years as an employed grocer, a lease opportunity, €40k of savings — the
  capital figure is pinned).
- The clerk hired November 2026 gets a name and a shift (pinned: 8 hours a
  day, within 07–21 opening).

### 3.3 History — the chronology in owner voice

**Job:** give the analyst the timeline *as testimony*, so that every
structural break in the data has a candidate explanation on file — and one
event (§6) carries a wrong interpretation.

Pinned events that MUST appear, each in one to three sentences of owner
voice with his feeling attached:

1. Opening, January 2025 — the stock-up rush of the first weeks (this
   explains the January artifact; the owner remembers it as "everyone
   trying us out at once").
2. The energy-crisis autumn of 2025 — suppliers' invoices, the electricity
   bill.
3. February 2026 — the freezer died overnight; the whole frozen aisle and
   part of the dairy case into the bin; the €1,800 repair.
4. Summer 2026 — the heatwave; ice cream and spoiled produce.
5. September 2026 — the apartment building filled with new households.
6. November 2026 — the expansion: first employee, longer hours (07–21),
   deeper shelves; his pride in having saved for it.
7. January 2027 — the lease renewed at +12%; the first time the January
   tax bill and the new rent landed in the same month.
8. March 2027 — the discounter opened nearby (§6: this is where his wrong
   belief attaches).
9. May 2027 — his counter-attack: price cuts on drinks, snacks, household
   goods.
10. August 2027 — the street festival fortnight.
11. Autumn 2027 — staples got expensive again.
12. December 2027 — the books close on essentially zero; the lease decision
    for 2028–29 is due.

Never attach magnitudes the owner wouldn't quote; "the rent went up twelve
percent" is fine (it's his contract), "visits fell 4.8%" is not (he can't
know that — measuring it is the analyst's job).

### 3.4 Operations & business model

**Job:** the facts an intake interview would establish, so the analyst
doesn't waste Layer-1 effort discovering the mundane: opening hours (08–20,
then 07–21 from November 2026), closed Jan 1 and Dec 25 only, Wednesday
deliveries, one supplier, monthly stock counts, the last-Sunday discount,
card-or-cash till, no delivery service, no online anything.

### 3.5 The data handover + the confessions

**Job:** list the files in plain language (a one-line data dictionary per
file), then have the owner *confess the known messes* — a real client
always warns you:

> "The POS has re-uploaded receipts before, I never found them all. The
> month-end count never quite matches what the book says. Some delivery
> paperwork never got typed in — I paid for goods you won't find invoices
> for."

Rules: confessions calibrate expectations but never give locations, counts,
or amounts ("some", "sometimes", "never quite"). One confession per major
defect family the analyst will meet in Layer 0; no confession for the
subtle ones the case wants them to *find* (the label drift, the snapshot
typos stay unannounced).

### 3.6 The ask

**Job:** a presenting problem, a deadline, and tiered questions in owner
language, each with a deliverable he would recognize.

- The presenting problem (pinned, and it must lead): *record revenue,
  three years of growth, and essentially no profit in 2027 — the lease
  renewal decision is due.*
- Tier the questions descriptive → diagnostic → predictive → prescriptive.
  Six to ten total; each phrased as the owner would ask it; each silently
  mapped (in the appendix, not the brief) to catalog rows. For the
  canonical baseline the spine is:
  1. "Show me where the money actually goes." (L1)
  2. "Am I really growing, or does it just feel that way?" (7.1)
  3. "What is this 'shrinkage' costing me and should I be worried about
     theft?" (0.5)
  4. "What did the discounter actually cost me?" (7.3 — the mis-framed one)
  5. "Was hiring, and everything that came with it, worth it?" (7.9)
  6. "Which customers am I losing, and who replaced them?" (7.2)
  7. "What should I expect next year to look like?" (L3)
  8. "Renew, close, or change something — what do the numbers say?" (7.11)
- State what a deliverable looks like in his terms ("a page I can read",
  "a number with your confidence in it"), and what he can pay attention
  to — the case should discourage 40-page decks by construction.

### 3.7 Stakes and success criteria

One short section: what happens if he renews blindly (two more years of
rent against a −€481 year), what he thinks success looks like, what the
engagement's real success looks like (a corrected diagnosis). Keep the gap
between those two implicit — that gap is the case.

## 4 The wrong-belief device

Every case carries **exactly one** load-bearing false belief, stated with
full conviction in the owner's voice, satisfying all four conditions:

1. **Plausible** — a reasonable person with his information would believe
   it. (Canonical: "the discounter is killing me. Everything was perfect
   until March 2027.")
2. **Testable** — the visible data plus honest methods can interrogate it.
3. **Correctable** — the dataset's ground truth (twins, answer keys) can
   grade whether the analyst overturned it. (Truth: the entry cost ~€6k of
   2027 profit; his own expansion cost an order of magnitude more.)
4. **Consequential** — believing it leads to the wrong decision (he is
   considering NOT renewing the lease, fleeing a competitor, when the
   numbers say: renew, fix the payroll).

Never plant more than one; a client who is wrong about everything teaches
cynicism, not method.

## 5 Consistency rules and the QA sweep

Before a brief ships, run these checks — mechanically, against the data:

1. **The contradiction sweep.** Every factual claim in the brief must be
   query-verified or query-neutral. Opening hours, closure days, delivery
   weekday, event dates, the discount Sunday, staffing dates: check each
   against `visible/` with an actual query, not from memory.
2. **The precision audit.** Scan every number in the brief: is it something
   the owner would know at that precision? Round to owner-memory precision
   (rents and repair bills exactly — he signed them; revenues to the
   nearest ten thousand; percentages only when contractual).
3. **The vocabulary scan.** Grep the brief for the banned designer terms
   (§2) and for `hidden/` filenames.
4. **The vintage check.** Regenerating data can move emergent details (which
   months spike, exact counts). Prefer *mechanism phrasing* over specific
   months for anything emergent; keep specific dates only for scripted
   events, which are stable per seed. Re-run the sweep after any
   regeneration.
5. **The explanation audit** (reverse direction): list the dataset's ten
   most prominent quirks (from the Layer 0–1 notebook); confirm each has a
   narrative hook in the brief — a trait, an event, or a confession. A
   quirk with no hook is fine only if *discovering it unprompted* is part
   of the pedagogy (label drift, typos).

## 6 The instructor appendix — contents

1. **The mapping table**: each brief question → catalog row(s) → grading
   source (answer-key file or twin arm) → what a full-credit answer
   contains.
2. **The trap list**: every planted misdirection the case activates, each
   with its tell and its resolution (for the baseline: the January
   cold-start artifact, the schedule-composition heatmap, the "theft" that
   is a typist, the invisible entry, the owner's mis-framed blame, the
   markdown machinery that went silent after 2025).
3. **Reveal staging**: distribute in three stages — (a) brief + `visible/`
   only; (b) after attempt: the graded notebooks; (c) last: `hidden/` and
   the twins. Never bundle stage-c files with stage-a.
4. **Rubric hooks**: per question, the 2–3 binary checks that separate
   "did the work" from "got the point" (e.g., for the discounter question:
   did they refuse the naive before/after? did they build a counterfactual?
   did they challenge the client's framing?).

## 7 Voice and form

- Genres that read as real: a **letter/memo from the owner** (the ask), an
  **intake-interview transcript** (persona, history, confessions — Q&A
  format hides exposition naturally), and a **one-page data dictionary**.
  Avoid textbook third-person omniscience.
- Length: the whole brief fits in 3–5 pages. A case the analyst won't
  reread is a case that doesn't work.
- The owner's register: concrete, mildly opinionated, numerate about money
  he handles, vague about statistics. He says "Saturday mornings are a
  madhouse", not "weekend footfall exhibits a bimodal peak".

## 8 Generalizing to other arms (and the configurator)

Because every scenario is a declarative spec, the case pipeline is:

1. **Pinned-fact extraction**: from the spec (scripted events, policy
   changes, horizons) and from cheap queries on the arm's `visible/`
   (opening hours, staffing dates, per-year revenue rounded).
2. **Event rendering**: each spec entry maps to an owner-voice sentence
   template (a cost event → "my supplier's prices went mad for a couple of
   months"; a `weather_edit` → "that summer was brutal"; a policy change →
   "I hired/extended/closed..."). Maintain the template table alongside
   `SCENARIOS`.
3. **Free-element reuse**: brand, persona, and town stay CONSTANT across
   arms — the same shop living different histories — so students can carry
   context between exercises and twins stay narratively coherent.
4. **Wrong-belief selection**: choose the belief the arm's twins can grade
   (each reference arm should declare its candidate in the appendix).
5. **QA sweep** (§5) runs per generated case, always.

Hand-write the canonical `3y_baseline` case first; treat it as the gold
standard the templates must be able to reproduce.

**Package amendment: the configurator now exists, for live runs.**
`package/grocery_sim`'s `sim.describe()` (`persona.py` + `describe.py`) is a
working instance of the pipeline sketched above — letter, intake-interview
Q&A, and questions, auto-generated from a run's real `settings` and results —
but built for a different surface than this section anticipated: it narrates
any `GroceryStoreSimulation` a caller sets up on the fly (any combination of
`settings.events`/`potential_investment`), not the pre-generated
`data/scenarios/`/`cases/` arms this guide's pipeline targets. Two differences
worth naming: `describe()`'s owner identity (`persona.py`) is drawn fresh
per run from the settings' random seed, so it does **not** hold brand/persona/
town constant across arms the way step 3 above prescribes for the hand-cased
family; and `describe()`'s tone is situationally aware — it classifies the
run's real profit trajectory (`_financial_situation()`: struggling / thriving
/ uncertain) and frames the letter, the Q&A, and the ask accordingly, rather
than assuming the "wrong belief to grade" framing this guide's step 4 asks a
case-writer to choose deliberately. The two systems solve related but distinct
problems: this guide's pipeline is for curated, reused teaching cases;
`describe()` is for narrating an arbitrary one-off simulation the moment it
finishes running.
