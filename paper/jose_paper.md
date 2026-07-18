---
title: 'grocery_sim: A Structural Microsimulation with a Known Causal Ground Truth for Teaching Business Analytics'
tags:
  - Python
  - data science education
  - business analytics
  - simulation
  - causal inference
authors:
  - name: ChinhMai
    orcid: TODO — add your ORCID iD (https://orcid.org)
    affiliation: 1
affiliations:
  - name: TODO — your affiliation, or "Independent Researcher" if none
    index: 1
date: TODO — submission date
bibliography: jose_paper.bib
---

<!--
Draft JOSE (Journal of Open Source Education, https://jose.theoj.org)
submission. Structure and section headers follow JOSE's own paper
template and review checklist as of this draft; verify both against
JOSE's current author guidelines before submitting, since journal
requirements can change.

This is a companion, non-technical paper. The full mathematical
treatment — every distributional choice, the MILP opening decision, the
phase-by-phase construction — lives in `paper/paper.pdf` and is cited
here rather than repeated. This file should stay short (JOSE papers are
typically 1000-2000 words); if it starts growing past that, cut rather
than compress.

Every [TODO] marker below (and in jose_paper.bib) needs your attention
before this is submittable — see the note at the end of this file for
the full list.
-->

# Summary

`grocery_sim` is a Python package that simulates one to three years in
the life of a small neighborhood grocery store — its customers, its
owner, a calendar of weather and macroeconomic events, a daily market,
and the full paper trail a real shop produces (till receipts, supplier
invoices, price histories, a monthly ledger, a tax filing). Unlike a
dataset sampled from convenient distributions, every number the package
produces has a documented, traceable cause: prices respond to costs,
costs respond to scripted shocks, customers respond to prices according
to individually varying preferences, and the owner responds only to what
they can actually observe, which is never the same as the full truth.
That gap — between what the owner believes, what actually happened, and
what a perfectly informed operator could have achieved — is not injected
noise; it is the mechanical output of a fully specified, inspectable
model. Each simulated run also ships with a reproducible, fictional
owner narrating that run's own real events and results as a short
business-case brief, giving a learner a concrete, plausible-but-testable
starting point for analysis rather than a bare set of CSV files.

# Statement of Need

Teaching applied data analytics — the kind of course that asks a student
to clean messy records, diagnose a cause, forecast a trend, or evaluate
a business decision — runs into a persistent materials problem. Real
business datasets, when they are available at all, come with no known
ground truth: an instructor cannot tell a student whether their causal
claim is *correct*, only whether it is *plausible*, because nobody
knows the real generating process either. Purely synthetic datasets
solve the ground-truth problem but usually at the cost of realism: rows
sampled independently from fitted distributions have no causal
structure to discover, no owner's blind spot to uncover, and no honestly
messy paperwork to reconcile before the "real" analysis can start.

`grocery_sim` is built to occupy the middle ground those two options
leave empty. It generates data from an explicit, documented mechanism —
so every question an instructor might ask ("was the expansion worth
it?", "what did the competitor actually cost?") has a computable, exact
answer available via a counterfactual replay — while still producing
data that looks and feels like a real small business's records,
imperfections included. Because a fresh run is generated (not looked up)
from a settings dictionary and a random seed, an instructor can produce
a new, never-before-seen dataset and case brief for every student, every
term, or every assignment variant, without hand-authoring a new case
each time.

The intended audience is instructors and self-learners in business
analytics, applied statistics, and introductory data science who want
exercises with a real answer key behind them, and who want to assign a
different, freshly generated dataset to every student rather than
reusing one static file that answers eventually circulate for.

# Design: a scripted macro layer, an emergent micro layer

The package is built from two layers that are only ever allowed to
interact in one direction. A **scripted, exogenous layer** — the
calendar, the weather, and macroeconomic events such as a supply shock,
a tax change, or a competitor's entry — is decided in advance and is
completely independent of anything the simulated customers or owner do.
An **emergent, endogenous layer** — individual customers making a
discrete choice at the shelf, and an owner following fixed heuristic
restocking, pricing, and (if permitted) expansion rules in response to
what they actually observe, never to the ground truth — produces
everything else.

Nothing in the package lets an event in the first layer be *caused* by
anything in the second, and nothing lets one scripted event trigger
another automatically: a macro "shock, then a policy response two months
later" story has to be authored as two separately dated entries by the
person configuring the run. This restriction is deliberate rather than a
limitation. Because the exogenous layer never depends on simulated
behavior, two runs that differ only in one event being present or absent
are otherwise identical — the same customers make the same choices on
the same days — so the difference between the two runs is an *exact*
causal effect, not a correlation estimated under uncertainty. This is
the same property `describe()` (below) relies on internally.

# The object API

```python
from grocery_sim import GroceryStoreSimulation

sim = GroceryStoreSimulation()
sim.setup(settings)     # validate a settings dict (events, investments, ...)
sim.simulate()           # build the world, run the year(s), self-validate
sim.data()               # receipts, invoices, the ledger, the tax filing, ...
sim.describe()           # a persona-narrated business-case brief
sim.create_analysis(path)  # a scaffolded marimo notebook for the analysis
```

`simulate()` runs an automatic, tiered validation battery on every call —
structural bookkeeping identities that must always hold, one core check
comparing a perfectly-informed operator's profit against the
realistically-forecasting owner's, and calibrated realism bands — and
raises an error rather than silently returning inconsistent data if a
structural invariant breaks. The full settings schema, method reference,
and validation tiers are documented in the package's own README
[@grocery_sim_repo].

# A generated backstory, not just a CSV

`describe()` builds a small, reproducible fictional persona (a name,
age, and prior career — cosmetic identity only, keyed off the run's own
random seed) and narrates that run's *real* settings and results as a
letter and a short Q&A-style intake interview: which events happened and
when, what an investment cost and whether it paid for itself, and an
honest note about the records' own imperfections (a doubled receipt, a
gap in a weather log) computed directly from the exported tables, never
invented. When the owner's narrated belief about the cause of a bad year
is one of the model's own scriptable shocks, `describe()` silently runs
one counterfactual twin — the same settings and seed, with that event
removed — to decide, honestly, how confidently the brief's closing
section should read, without ever printing the underlying computed
number. The effect is a starting hypothesis a learner can either confirm
or overturn with the data itself, modeled loosely on the "first guess,
then verify" structure of a real analyst engagement, rather than a
dataset with no story attached at all.

# Learning objectives

Coursework built on `grocery_sim` output can target, among others:

- Reconciling imperfect records (duplicate postings, voided till lines,
  missing invoices) against an authoritative ledger before any analysis
  can begin — a skill real analyst work requires and clean textbook data
  never exercises.
- Distinguishing a genuine causal effect (measurable exactly via the
  package's own counterfactual replay) from a plausible-sounding
  narrative the data may or may not actually support — directly
  exercised by the owner's own narrated, sometimes-wrong belief in
  `describe()`'s brief.
- Standard applied-analytics tasks — trend and seasonality decomposition,
  shrinkage/loss analysis, customer churn, and a capital-investment
  evaluation — against data with a documented rather than assumed
  generating process.

# State of use

[TODO: this section is the part JOSE reviewers weight most heavily and
currently has no real content. Fill in honestly — e.g., "this package
has not yet been piloted in a classroom; it is submitted as
newly-available course material" if that is the true current state, or
describe an actual course/workshop it has been used in if one exists by
the time of submission. Do not leave a vague or evasive version of this
section — it is better to state a genuine "not yet piloted" than to
imply usage that has not happened.]

# Testing and validation

The package ships a `pytest` regression suite (settings-validation
errors, the persona/pronoun logic in isolation, and full simulations
across individual and combined events, investments, and random seeds)
that runs automatically in CI on every change, alongside the runtime
validation battery described above that checks every generated dataset
for internal consistency, not only the code that produces it.

# Acknowledgements

[TODO: add any acknowledgements — advisors, early readers, students who
piloted an exercise, etc. Leave this section out entirely if there is
nothing to add; do not fabricate content for it.]

# References

<!--
Consolidated TODO checklist before this is submittable:

1. Frontmatter: ORCID iD, affiliation, submission date.
2. "State of use" section: state honestly whether this has been piloted
   in an actual course/workshop, or that it is newly-available material —
   this is the section JOSE reviewers weight most heavily; do not leave
   it vague.
3. jose_paper.bib: fill in the grocery_sim_repo entry (repository URL,
   and decide whether to mint an archived DOI via Zenodo/Software
   Heritage before submitting -- JOSE typically expects an archived,
   versioned release, not a bare live GitHub link).
4. Add and verify any related-work citations yourself (synthetic data
   generation, structural/agent-based microsimulation, the business
   case method) -- none are included here since fabricating
   bibliographic details without being able to verify them live would
   risk citing something inaccurately. paper.pdf's own literature review
   (Section 2) is a reasonable starting point for which claims need one.
5. Acknowledgements: fill in or delete the section entirely.
6. Re-check this whole structure against JOSE's current author
   guidelines and review checklist at https://jose.theoj.org before
   submitting -- journal requirements can change after this draft.
7. Decide on final word count -- JOSE papers are typically short
   (~1000-2000 words); trim if this draft has grown past that once the
   TODOs above are filled in.
-->

