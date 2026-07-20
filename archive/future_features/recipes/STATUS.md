# Recipe-based scenario generation — parked

Shelved 2026-07-20, to revisit once there's time to design the
scenario-realism version properly rather than ship the narrower one.

## What this is

An early version of "let a caller request a specific `describe()`
task_type (`diagnose`/`optimize`/`invest`) instead of getting one at
random." `recipes.py` holds four hand-picked settings+seed combos, each
empirically verified (by `test_recipes.py`, running the real simulation)
to land on its claimed task_type.

## Why it's parked, not deleted

- **A real bug in the `invest` recipe.** Its settings never set
  `basic.retain_earning = True`, so the simulator's own retained-earnings
  mechanism (`retain_ratio`, the three investment thresholds) stays
  disabled — confirmed by running it: `retained_earnings` freezes at a
  one-time snapshot the moment the books "formalize," `capex` stays 0.0
  for the entire 3-year run. `describe()` still labels it "invest"
  because its check only reads that frozen balance against the smallest
  investment's capex — the label is true of the snapshot, not of
  anything the simulation actually did. Needs
  `basic.retain_earning: True` added, then the existing seed (300)
  needs re-verifying against the changed dynamics (a real threshold
  trigger could spend the balance back down before year-end).

- **The bigger open design question**: settings were seemingly chosen to
  *reliably hit a label* (e.g. `optimize` stacks a typhoon and a VAT cut
  in one year, plausibly because that combination is known to push
  shrinkage over the 6.5% cutoff) rather than chosen as an independently
  realistic teaching scenario that a seed search was then run against.
  For real classroom use the settings should be the pedagogical content
  (a specific, meaningful shock or story) and the seed search should be
  a secondary step layered on top — not the other way around. That also
  means not every scenario will be able to hit every label (a war-driven
  cost shock scenario may never produce "thriving with idle capital," no
  matter the seed), which is a real, useful constraint to design around
  rather than route past.

- **Cost**: each seed is a real multi-year simulation, roughly a minute
  of wall time. A proper per-scenario, per-label search (rather than
  one seed per label) is bounded but not free — worth scoping which
  scenarios/labels are actually needed before running it wide.

## What's here

- `recipes.py` — the `RECIPES` dict + `get_recipe()`/`list_recipes()`,
  as it stood when parked.
- `test_recipes.py` — the verification suite (8 tests, all passing at
  time of parking, including the broken `invest` case, which passes
  because it's only checking the label matches the frozen-snapshot
  read, not that an investment happened).

## Before resuming this

1. Fix `invest`'s settings (`retain_earning: True`) and re-verify.
2. Decide whether scenario-realism (settings chosen for teaching value
   first, seed search second) is a hard requirement or whether
   "one verified example per label" is good enough for the near-term
   need.
3. If pursuing scenario-realism, budget real simulation time for the
   search — see the cost note above.
4. Whichever direction: `recipes.py` is currently missing from
   `grocery_sim/__init__.py`'s module docstring, and
   `documents/CASE_WRITING_GUIDE.md` doesn't mention it despite
   `recipes.py`'s own docstring pointing there — both need closing
   before this ships.
