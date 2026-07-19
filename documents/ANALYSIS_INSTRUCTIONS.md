# Analysis Instructions — How to Work Through Each Layer

This is a method guide, not an answer key. `ANALYSIS_CATALOG.md` lists the
actual questions, the specific technique each one calls for, and exactly
what to grade your answer against; `ACCOUNTING.md` has the full
reconciliation contract; `CASE_WRITING_GUIDE.md` covers the case-brief
device. This document sits alongside them and answers a narrower
question: *for each of the eight layers, what is the general process,
what does each modeling technique actually buy you, and why is it the
right tool here rather than some other one* — independent of which
specific question in that layer you happen to be working.

Where a layer calls for a real statistical or econometric model, this
guide tries to explain the intuition first, in plain language, the same
way you'd explain it to a colleague before writing any code — not just
name-drop the technique. If you already know a method well, skip its
intuition paragraph; if you don't, that paragraph is the point of this
document.

It applies whichever way you got the data: a pre-generated arm under
`data/scenarios/<arm>/` (`visible/` to work from, `hidden/` to grade
against), or a run you simulated yourself with the `grocery_sim` package
(`sim.data()`, `sim.db()`, and `sim.data(include_hidden=True)` for the
same visible/hidden split). Everything below assumes you have both.

---

## Layer 0 — Clean the records before trusting them

The goal is a version of the data you can trust for every later layer —
nothing here is optional groundwork, it *is* the first layer, and every
technique here is bookkeeping logic rather than a statistical model:
there is a single correct answer to check yourself against, not an
estimate with uncertainty around it.

1. **Treat `cost_sheet` as ground truth for money.** Every other document
   — receipts, invoices — is paperwork you reconcile *to* it, not the
   other way around. The reason this direction matters: the ledger is
   the one document a real owner reconciles their own bank statement
   against every month, so if anything disagrees with it, the ledger
   wins and the disagreement is what you're hunting for.

2. **Duplicate receipts — the all-even rule.** The intuition: if a
   receipt got uploaded twice by a retrying terminal, every line on it
   now appears an even number of times (twice, or four times if it
   happened twice), and the *sum* of those duplicated lines is exactly
   double the real sale. So group receipt lines by whatever should have
   been a unique key (the same receipt id, the same product, the same
   quantity and price) and look for exact-multiple repeats — not just
   "this looks suspicious," but a repeat count that is itself a multiple
   of 2. That arithmetic signature is what lets you dedupe *mechanically*
   rather than by judgment call, and it's also exactly why the rule is
   called "all-even": a genuine single sale never repeats this way, and
   a corrected mis-ring (see the next point) creates an *odd* residual
   (one plus-line, one matching minus-line, netting to one real
   transaction), which is the tell that distinguishes the two cases.

3. **Voided mis-rings vs. real refunds.** A cashier's on-the-spot
   correction (scan the wrong item, immediately void it, re-ring the
   right one) and a customer returning a purchased item days later are
   both negative-quantity lines in the raw data, but they mean opposite
   things for revenue: one never really happened (net zero), the other
   is a real, later reversal of a real earlier sale. The distinguishing
   fact is a *reference*: a genuine refund points back at the receipt id
   of the original sale; a same-day corrected mis-ring does not,
   because there was never a separate, valid original transaction to
   point back to. Partition on that reference column before you compute
   anything involving revenue — conflating the two either overstates
   revenue (treating a real refund as a wash) or understates it
   (treating a mis-ring as a real lost sale).

4. **Invoices.** Deduplicate on the natural key (product, quantity, unit
   cost, order date, delivery date) — a legitimate second invoice for
   the same product would differ in at least one of those fields, so an
   exact match on all of them is a duplicate posting, not a coincidence.
   What's left over after deduping, compared against `cost_sheet`'s own
   procurement line, tells you whether anything is still missing
   (goods paid for but never logged) rather than just doubled.

5. **Inventory — the day-over-day identity.** Physical stock obeys a
   simple accounting identity every single night: today's book count
   should equal yesterday's, plus what was delivered, minus what sold,
   minus what was written off. This identity is the whole test — you
   don't need a statistical model to find inventory errors, you need to
   evaluate one equation per product per day and see where it fails to
   balance. The one nuance: a break that self-corrects the very next
   night is a counting typo (someone mis-keyed a shelf count and the
   next night's real count fixes it); a break that persists is a real,
   unexplained drift and deserves more attention.

6. **Write-offs: two different quantities, never summed.** A write-off
   tagged as spoilage is a report of real physical loss; a write-off
   tagged as a month-end stock-count correction is a report of
   *bookkeeping* drift (the count and the books disagreed, and someone
   reconciled them). These measure genuinely different things — real
   waste versus paperwork catching up to reality — and adding them
   together would double-count the same euros in one case and invent
   loss that never physically happened in the other.

7. **Standardize label noise.** Inconsistent payment-method spellings, an
   hour value of `0` (a placeholder for a lost timestamp — see the
   dedicated note on this below — never a literal midnight sale), a
   mistyped category on a promotions row, and gaps in the weather log
   are all low-rate injected defects, not signal. Normalize them before
   any downstream analysis groups by these fields, or you'll silently
   split one real category into two.

8. **Only once all of the above is done, run the reconciliation
   contract.** `ACCOUNTING.md` states, line by line, exactly which
   totals are supposed to tie to the cent after cleaning and which small,
   documented gaps are *expected* to remain by design. Treat this as
   your unit test suite for Layer 0 — passing it is how you know you're
   actually ready to move to Layer 1, not just how confident you feel.

**Watch out for:** the temptation to force every irregularity to zero.
Some gaps (the weather station's own outages, for instance) are
genuinely missing data and should stay missing rather than get imputed
away — inventing a plausible-looking value where the real answer is "we
don't know" is itself a data-quality error, just a quieter one.

---

## Layer 1 — Describe the business

The goal is to characterize the business honestly before asking *why* it
looks the way it does. Nothing here needs inferential statistics yet —
the discipline is restraint, not technique: describe only what the data
actually shows, and flag (don't yet explain) anything that looks like it
needs a cause.

- **A plain profit-and-loss**, built directly off `cost_sheet`: revenue,
  procurement, rent, wages, the tax lines, in that order, before
  anything more advanced. If this doesn't reconcile cleanly, Layer 0
  wasn't actually finished.

- **Shopping-time profiles** (day-of-week, hour-of-day) from `receipts`.
  Read these as evidence of *scheduling* — when people chose to come in,
  given the routines and constraints already baked into their lives —
  not automatically as evidence of a deeper taste. The intuition worth
  internalizing here: a peak at 6pm on weekdays doesn't mean people
  *prefer* evening grocery shopping in some abstract sense, it means
  most people are at work until then. Conflating "when people showed up"
  with "when people want to shop" is a subtle category error that
  Layer 2 will force you to confront properly.

- **Seasonality per category**, and separately for any narrow product
  type whose pattern might be getting averaged away inside a broader,
  flatter category (ice cream inside "frozen," say). The reason to check
  both levels: an aggregate index can hide a strong narrow effect simply
  by averaging it against everything else in the same category that
  doesn't move the same way.

- **Basket composition**: size and value distributions, and which
  categories tend to co-occur on the same receipt. This is purely
  descriptive co-occurrence (a contingency table or a simple lift
  statistic between category pairs) — save any causal claim about *why*
  two categories co-occur for Layer 2 or Layer 6.

- **Customer segmentation, but not one bucket for everyone.** The
  card-carrying panel supports genuine per-customer analysis (an RFM
  cut — recency of last visit, frequency of visits, monetary value per
  visit — is the standard, simple starting point: it needs no model,
  just three sorted numbers per customer, and it's usually enough to
  separate "regulars," "fading regulars," and "occasional shoppers"
  into visibly different groups). Anonymous cash traffic cannot be
  segmented this way at all — there's no stable identity to attach a
  history to — and a one-off guest token is a different kind of customer
  than a regular, not a regular with a short history. Forcing all three
  into one segmentation will just blur the boundaries between them.

- **Pricing architecture**: how often shelf tags actually change
  (repricing cadence) and where the price endings cluster (charm
  pricing). Both are simple frequency counts, not models — the value is
  in noticing the pattern exists at all before Layer 2 asks what drives
  a *specific* repricing event.

- **Stockouts and spoilage**, measured descriptively (incidence rates by
  product and month) before diagnosing either one's cause.

- **Effective tax rate**: the rate actually remitted divided by revenue,
  which can differ from the nominal rate on the books once category mix
  and timing are folded in.

**Watch out for:** crediting every visible pattern to a real preference.
A category can show something that looks exactly like seasonality purely
because other categories are competing for the same fixed weekly
household budget during *their* high season — a customer who spends more
on holiday baking in December has less left for something else that
month, which shows up as a dip in the "something else" category with no
change whatsoever in how much anyone actually wants it. Before crediting
a pattern to genuine preference, check whether it survives once you
account for that budget-crowding effect (Layer 2 has the tools).

---

## Layer 2 — Diagnose causes

This is the layer where technique choice actually matters, because the
question changes from "what happened" to "why," and "why" claims are
wrong far more easily than they sound. The organizing idea behind every
method below is the same one the whole simulation is built around: a
variable that is decided *in advance and independently of the shop's own
behavior* (weather, a macro shock, the calendar) can be used as a clean
source of variation to isolate a causal effect, because nothing the shop
does could possibly have caused *it* — the causal arrow only runs one
way. A variable the owner or customers actually react to (a price, a
promotion, a stocking decision) cannot be used this way without more
care, because it's tangled up with everything that made the owner or the
customers act.

- **Does weather move the business? — regression with calendar
  controls, robust errors.** The naive version — just correlate revenue
  with rain — is confounded by season: it rains more in some seasons
  than others, and demand also varies by season for reasons that have
  nothing to do with rain, so a raw correlation mixes the two together.
  Calendar controls (day-of-week and month or seasonal-cycle dummies)
  soak up the part of the variation that's just "it's winter," leaving
  the weather coefficient to capture only the part of the day-to-day
  wiggle that weather itself explains. Separately: daily revenue is
  autocorrelated (a slow week tends to stay slow for a few days), which
  doesn't bias the *coefficient* but does bias plain OLS standard
  errors downward — you'll think you're more confident than you are.
  Use heteroskedasticity-and-autocorrelation-consistent (HAC / Newey-West)
  standard errors, which widen your confidence intervals to reflect that
  correlation honestly instead of pretending each day is an independent
  draw.

- **The rebound effect.** A rained-off shopping trip doesn't vanish
  demand, it usually just delays it — the customer needed groceries
  regardless of weather, and buys them a few days later instead. If you
  only look at the day of the storm, you'll see a dip and conclude
  weather destroys demand; look a few days past it as well, and you'll
  often see a partly-offsetting rebound. The honest measure of a weather
  event's cost is the *net* effect over a short window, not the single
  worst day.

- **How fast does a cost shock reach the shelf? — pass-through /
  event-study regression.** The owner doesn't reprice the instant a
  supplier invoice changes; a real shopkeeper smooths and delays,
  watching a trend before committing to a new tag. An event-study design
  (align every cost shock to its own start date, then look at the
  average price response at each day or week afterward, across
  multiple shocks) directly shows you the *shape* of that lag — a flat
  period, then a jump, then a plateau — which a single before/after
  comparison would flatten into one number and hide.

- **Does a price increase lose customers, or just move them? — instrumented
  elasticity vs. a naive comparison.** A plain regression of quantity on
  price is contaminated by simultaneity: if the owner raises a price
  *because* he sees strong demand, high price and high quantity will
  appear together even though the true demand curve slopes down — the
  naive regression can even come out with the wrong sign. The fix is an
  instrument: a variable that moves price but has no direct effect on
  demand except *through* price (the exclusion restriction). A wholesale
  cost shock is a good candidate, because a shock to what the shop pays
  its supplier changes what it charges customers, but doesn't itself
  change how much any customer wants the product. Two-stage least
  squares formalizes this: first predict price from the instrument
  alone, then regress quantity on that *predicted* price rather than the
  raw one, which strips out the part of the price movement that was
  actually a reaction to demand. Do this at the SKU level, and separately
  do a much simpler category-level comparison with no instrument at all
  — where the two disagree is itself informative: it usually means
  customers are substituting to a close neighbor rather than actually
  buying less overall, which a SKU-level number alone can't tell you.

- **Is my instrument actually valid? — check the exclusion restriction
  directly, don't assume it.** An instrument needs two properties:
  it has to actually move the variable you care about (relevance —
  usually easy to check, just look at the first-stage regression), and
  it must have *no other channel* into the outcome except through that
  variable (exclusion — this is the one people skip, and the one that
  actually breaks analyses). A scripted energy crisis is a good
  illustration of exactly this failure: it raises wholesale costs (so it
  looks like a fine price instrument) but it *also* squeezes household
  heating bills at the same time, which squeezes the same households'
  grocery budgets directly — a second channel into demand that has
  nothing to do with the shop's own price. Using it as a price instrument
  without checking this would attribute some of that budget-squeeze
  effect to price sensitivity that isn't really there. An idiosyncratic,
  narrowly-targeted cost event (one that doesn't plausibly touch anyone's
  wallet directly) is the cleaner instrument to reach for instead.

- **Did the markdowns actually work? — difference-in-differences, and
  why selection breaks it.** A markdown campaign here is *triggered* by
  a product already sitting in overstock, and overstock is itself
  correlated with the product already selling slower than the owner
  expected. That means the products that get marked down were already
  on a declining trend *before* the discount — the key assumption behind
  a simple before/after or difference-in-differences comparison
  ("parallel trends": absent the treatment, the treated group would have
  moved in parallel with an untreated comparison group) is violated by
  construction. A naive lift estimate will understate the campaign's
  effect, because it's comparing against a "no-treatment" baseline that
  was already falling. The store's separate, calendar-triggered
  storewide discount (the same date every month, chosen with no
  reference to any product's own recent trend) doesn't have this
  problem at all, and is the clean anchor to calibrate a markdown-lift
  estimate against before trusting it on the selection-biased campaigns.

- **Spoilage drivers.** Relate write-off rates to temperature and to any
  live cost/energy shock in the same regression, since both can move
  spoilage simultaneously (heat directly speeds spoilage; an energy
  shock can degrade cold-chain reliability) — attributing a spike to only
  one of them when both are active will overstate that one's effect.

- **Is card data representative? — test the missingness mechanism, don't
  assume it.** The concern is whether card-paying customers look
  different from cash-paying ones (different basket sizes, different
  price sensitivity), which would make conclusions drawn only from the
  visible card panel misleading about the whole customer base. The test
  is direct: compare observable basket characteristics (size, category
  mix, timing) between card and cash transactions on the same days,
  the same way you'd test for "missing at random" in any partial-data
  setting. If they look statistically indistinguishable, the card panel
  is a fair sample of behavior even though it can't identify every
  individual; if they don't, any customer-level model has a real
  selection problem to account for.

- **Refunds and shrinkage as rates, not constants.** Model these as a
  rate that can vary over time and by category rather than assuming one
  fixed number for the whole period, and specifically check for an edge
  effect near the very end of the observed window (a refund with a
  multi-day return delay may not have happened yet within the data's own
  horizon, which will make the last week or two look artificially clean).

- **Small samples deserve honesty, not false precision.** An effect like
  a single specific holiday's own demand bump has, at most, a handful of
  real occurrences across the whole observed period. Report it with a
  correspondingly wide interval and say plainly that the estimate is
  based on very few events — a narrow-looking confidence interval built
  on nine data points is usually wrong about its own precision, not
  reassuring.

---

## Layer 3 — Predict

The goal is a forecast whose quality you can actually put a number on,
not just a plausible-looking curve.

- **Always benchmark against a naive baseline first.** A seasonal-naive
  forecast (this week's number is last year's same week, or last
  period's actual) is the bar any real model has to clear. The reason
  this matters more than it sounds: a sophisticated model that merely
  matches seasonal-naive isn't earning its complexity — the entire value
  of forecasting work is the *gap* above the naive baseline, so compute
  that gap explicitly rather than reporting only the fancy model's own
  error.

- **Respect time in every split.** A forecast evaluated on a random,
  shuffled train/test split will look better than it really is, because
  information from "the future" (relative to some point in the real
  series) leaks in through nearby dates in the training set. Use a
  genuine chronological holdout — train on the past, test on a later
  period the model never saw — every time.

- **Censored demand — why raw sales aren't the same as true demand.**
  When a product is out of stock, the recorded sale for that day is
  zero (or low), but the real *want* for it wasn't — it's just
  unobserved. A forecasting model trained naively on raw sales history
  will therefore systematically underestimate demand for anything that
  stocks out often, and can even go on to recommend ordering *less* of
  exactly the products that need more. The fix is conceptually the same
  as a Tobit or Heckman-style correction in econometrics: treat a
  stockout day's true demand as unobserved-but-bounded-below (you know
  it was at least what you sold, quite possibly more) rather than as a
  real, complete observation, and either model the censoring explicitly
  or reconstruct an uncensored demand series before forecasting from it.

- **Auditing the owner's own forecast.** To fairly critique a simple
  rule (like a trailing moving average), reconstruct it exactly as it
  would have run in real time — using only the information available up
  to each date, nothing later — then compare it three ways: against what
  actually sold, against the true underlying demand, and against your
  own model. A rule built on top of censored sales data (see above) will
  compound its own error into a self-reinforcing spiral: it under-orders
  because past sales looked low, which causes another stockout, which
  makes the next period's sales look low again. Naming that spiral
  explicitly is usually more valuable than any single accuracy number.

- **Stockout risk and early warning are classification problems, not
  regression.** The question is binary within a horizon ("will this SKU
  stock out in the next week?", "is this customer sliding toward
  leaving?"), so frame it that way: a probability of the event, judged
  by how well it ranks and calibrates against what actually happened,
  not by squared error against a continuous number nobody asked for.
  Because the event you care about is usually the minority class (most
  SKU-weeks don't stock out, most customers don't churn this month),
  plain accuracy is a misleading metric — a model that always predicts
  "no" can still score high accuracy while being useless. Look at
  precision and recall (or a ranked list: "here are the ten products
  most at risk this week"), not overall accuracy.

- **Know the limits of a short history, honestly.** A model trained on
  one year of data has seen exactly one Christmas and one summer. It
  structurally cannot yet tell a genuine multi-year trend apart from
  ordinary seasonal variation — there's only one cycle to learn from,
  so "the business is growing" and "this was just a good summer" are
  statistically indistinguishable with that little data. Say this
  explicitly rather than projecting confidently past what the data
  supports; a three-year run is the only way to actually test the
  claim, because only then do you have more than one seasonal cycle to
  compare against.

---

## Layer 4 — Prescribe

The goal is to turn a diagnosis into a decision and put a real euro
figure on it — every recommendation here should end in a number, not a
direction.

- **Frame every answer against the believed/realized/oracle triptych.**
  The model tracks three profit figures for a reason: what the owner
  believed going in, what actually happened, and what a
  perfectly-informed operator could have achieved with the same world.
  The gap between the second and third is the real, priceable value of
  better analytics or a better decision — quote that gap in euros, don't
  just argue that a change would probably help.

- **Ordering policy — the newsvendor intuition.** Every ordering
  decision under uncertain demand is a trade-off between two opposite
  mistakes: order too little and you lose a sale you could have made
  (understock cost); order too much and the excess spoils or sits
  unsold (overstock cost). The classic "newsvendor" result formalizes
  this as a single critical ratio — order up to the demand quantile
  equal to understock cost divided by the sum of understock and
  overstock cost — which is a useful mental anchor even if you don't
  fit the full model: a product that's cheap to overstock and expensive
  to run out of (a fast-moving staple with thin margin per lost sale
  relative to its holding cost) should be stocked deep; a product that's
  expensive to overstock (a perishable with a short shelf life) should
  be stocked lean, even at the cost of occasionally running out.

- **Repricing — act at the level you actually trust.** An elasticity
  estimated at the category level pools together enough transactions to
  be fairly stable; an elasticity estimated on one individual SKU is
  noisier and easier to get wrong, precisely because Layer 2 already
  showed you that individual products substitute for their close
  neighbors. Recommending a repricing action at a level finer than the
  one you can actually estimate reliably is the most common way a
  seemingly-rigorous prescriptive answer goes wrong in practice.

- **Assortment (delist/add) decisions — full cost, not just units
  sold.** A slow-selling product's true cost of staying listed includes
  storage and a per-listing fee, not just the shelf space; comparing raw
  unit sales alone ignores that a low-volume, low-carrying-cost item can
  still be worth keeping, while a modestly-selling but expensive-to-store
  item may not be.

- **Promotion policy — don't reintroduce the bias you just diagnosed.**
  If Layer 2 found that markdowns are triggered by overstock and
  therefore confounded with an already-declining trend, a redesigned
  trigger rule needs to break that same link (for instance, triggering
  on a demand-adjusted signal rather than raw stock cover) or it will
  just reproduce the identical measurement problem under a new name.

- **Staffing/hours decisions — complete costs against complete
  benefits.** Price the *full* employer cost of a hire (wages plus
  payroll tax, not wages alone) against the *full* recovered revenue,
  including demand that used to be lost simply because the shop was
  closed outside the old hours. Judging a hiring decision on partial
  figures on either side of that comparison will make it look better (or
  worse) than it really is.

- **Cash management as one policy, not three.** The credit facility, the
  VAT remittance schedule, and any accrued profit-tax liability all draw
  on the same pool of cash at the same time each month; treat working
  capital as a single planning problem rather than reasoning about each
  piece separately.

---

## Layer 5 — The policy laboratory

The goal is to measure a real causal effect *exactly*, using paired
scenario runs, and then use that exact answer as a scoring key for your
own diagnostic method from Layer 2.

- **Why CRN twins give you an exact answer instead of an estimate.**
  Every simulated draw in this model — a specific customer's decision on
  a specific day, a specific product's spoilage roll on a specific night
  — is keyed to a stable identity rather than pulled from one long,
  shared random sequence. That discipline (common random numbers, CRN)
  is what makes it possible to generate two runs — a baseline and an
  edited "twin," with exactly one thing changed (a tax rate, a shock, a
  hiring decision) — where every customer who is *not* directly affected
  by the edit makes the identical decision, on the identical day, in
  both runs. Because everything except the edit is held fixed bit-for-bit,
  any difference you observe between the two runs' outputs cannot be
  sampling noise or some other unrelated shift — it can only be the
  causal effect of the one thing that changed. This is the same logic
  behind a paired experiment in applied statistics (pairing cancels out
  everything the pair has in common, leaving only the treatment
  difference), just implemented exactly rather than approximately,
  because here you control the random seed instead of merely blocking on
  observed covariates.

- **The real exercise: validate your own method against the truth.**
  Don't just read off the twin difference and stop — first estimate the
  same effect *observationally*, using only the baseline arm and the
  techniques from Layer 2, exactly as you would if a twin arm didn't
  exist. Then compute the literal twin difference. Then compare the two
  numbers. If they're close, your observational method is trustworthy;
  if they diverge, that divergence is telling you something specific
  about a bias in your method (an invalid instrument, an unaccounted
  confound, a selection effect) that you now have the rare opportunity
  to actually diagnose, because you know the right answer. This
  comparison — not the twin difference by itself — is the actual point
  of this layer.

- **No new machinery beyond Layer 2.** The statistical techniques don't
  change; only the ground truth does, from inferred to exact. If you
  found yourself reaching for a new method here, that's a sign you
  should revisit whether the observational estimate in Layer 2 used the
  right one.

- **External validity — does a relationship estimated in one world hold
  in another?** Take a relationship estimated from one scenario's data
  (an elasticity, a pass-through rate) and use it to predict a
  *different* scenario's outcome, one it was never fit on. How close you
  land is a direct, quantified answer to "does this generalize," which
  is normally one of the hardest questions to answer honestly with real
  data, because you'd need exactly this kind of paired counterfactual to
  test it properly.

---

## Layer 6 — Advanced and structural

The goal is to recover the underlying preferences and structure directly
— the mechanisms the earlier layers only observed the consequences of —
and, where `hidden/` access is available, to check the recovered
structure against the true parameters, not just against how well the
model fits.

- **Discrete choice (conditional logit) — the random utility
  intuition.** A customer choosing among the products on a shelf is
  modeled as picking whichever option gives them the highest utility —
  a number combining how well the product matches their taste against
  how much they dislike its price — once a bit of unpredictable,
  person-and-moment-specific noise is added to every option. If that
  noise follows a particular, well-behaved distribution (a Gumbel
  distribution — the reason this specific choice matters is a genuine
  mathematical result, not an arbitrary convenience), the probability of
  picking each option collapses into a clean closed form: the softmax of
  the options' average utilities. That's the entire justification for
  fitting a conditional logit here: it isn't a convenient approximation
  bolted on afterward, it is the *exact* aggregate consequence of
  individually noisy, utility-maximizing shoppers, which means the
  parameters you recover (a price-sensitivity coefficient, a
  brand-affinity loading) are estimates of the same real quantities the
  simulation used to generate the choices in the first place — fit it on
  the card panel's purchase histories, and if you have `hidden/` access,
  compare your recovered price sensitivity distribution directly against
  the true one as the real test of whether the method worked, not just
  whether the log-likelihood looks good.

- **Partial pooling — the shrinkage intuition.** A single SKU's own
  sales history, especially a slow-moving one, is often too short and
  noisy to estimate its own seasonal pattern or price sensitivity in
  isolation — the estimate swings wildly based on a handful of unusual
  weeks. A hierarchical (multilevel) model addresses this by letting
  every SKU borrow statistical strength from its category: each
  product's estimate is pulled ("shrunk") toward its category's average,
  by an amount that depends on how much individual data that product
  actually has. A high-volume product with a long, clean history barely
  moves from its own raw estimate; a thin, noisy one gets pulled much
  closer to the category norm. The intuition to hold onto: this isn't
  "cheating" by borrowing other products' data, it's a principled
  admission that a noisy individual estimate is often a worse guess
  about the truth than a well-estimated group average is, and the model
  finds the right balance between the two automatically rather than
  you having to choose one extreme or the other by hand.

- **Marketing-mix decomposition — and its one sharp trap.** Decomposing
  sales into a base level plus additive or log-additive contributions
  from season, weather, price, promotion, and scripted events is a
  standard regression exercise once you've built the right feature set.
  The trap specific to this data (and to real marketing-mix modeling in
  general) is the same endogenous-response confound from Layer 2: if a
  promotion is itself *scheduled in reaction to* a shock (the owner
  loosens markdowns because a competitor just arrived, say), then a
  decomposition that treats "promotion" as an independent input will
  wrongly credit or blame the promotion for movement that was actually
  caused by the event that triggered it. Check the promotion calendar
  against the event calendar before trusting a clean separation between
  the two.

- **Decomposing hidden demand into its real causes.** The gap between
  recorded sales and true underlying demand isn't one thing — it's the
  sum of at least four distinct, separately-identifiable causes: a
  customer arriving outside opening hours, a stockout, an exhausted
  weekly budget partway through a shopping list, and the outside option
  simply winning on price or availability. Reporting one lump "missing
  demand" number obscures which of these actually matters most, and each
  one implies a completely different fix (extend hours vs. carry more
  safety stock vs. neither, since a budget-exhausted customer wasn't
  going to buy regardless of stock).

- **Separating regulars from passing trade — mixture models.** Rather
  than assuming every token in the panel belongs to one homogeneous
  population, a mixture model treats the panel as a blend of (at least)
  two latent groups — habitual regulars and one-off guests — each with
  its own typical visit pattern, and infers, probabilistically, which
  group each token most likely belongs to based on its observed
  behavior, without ever being told the true label directly. The
  intuition is the same as an unsupervised clustering algorithm with a
  probabilistic (rather than hard) assignment: a token that visits every
  week for months looks nothing like one that appears once and vanishes,
  and the model separates the two patterns automatically once you let it
  posit more than one underlying behavioral type.

- **Testing a causal graph against the data.** If you've committed to an
  explicit causal graph (which variables affect which others, and in
  what direction), that graph makes falsifiable predictions: specific
  pairs of variables should be statistically independent once you
  control for the right set of others (the graph's implied conditional
  independencies). Testing those specific relationships — not just
  eyeballing whether the graph "looks plausible" — is what makes the
  exercise a real test rather than an illustration; one of the
  independencies in this model's own documented graph is deliberately
  violated, specifically so that a careful check catches it rather than
  every graph passing automatically.

---

## Layer 7 — The three-year arc

Only meaningful on a three-year run. The goal is everything a single year
structurally cannot ask: real growth, real churn, real capital decisions
— each of which needs more than one seasonal cycle to even be
statistically askable.

- **Growth vs. season — trend-seasonal decomposition.** The underlying
  demand drivers in this model are constructed to average out to the
  same level every single year by design, which means any genuine
  multi-year growth you measure cannot be coming from the demand script
  itself — it has to be coming from somewhere else entirely: the
  customer panel's own arrival-and-departure dynamics, or ordinary cost
  drift. A classical decomposition (STL — seasonal-trend decomposition
  via loess, or simply comparing the same month year-over-year) splits a
  series into a smooth trend, a repeating seasonal component, and
  leftover noise; the reason you need *three* years rather than one or
  two is identification: with only one cycle, "trend" and "season" are
  statistically tangled together (a single summer's revenue could be a
  seasonal peak or the start of a rising trend, and you cannot tell
  which from one observation of it), and it takes at least a second
  full cycle to see the season repeat on its own and a third to
  confirm a trend is holding rather than reversing.

- **Churn — why this is a survival problem, not a simple count.** A
  customer who leaves the neighborhood doesn't announce it; their card
  token just stops appearing. That silence is exactly the setup a
  survival analysis is built for: each customer has a "time to event"
  (departure) that is only sometimes observed within your data window —
  many customers active at the end of the period simply haven't left
  *yet*, which is not the same statement as "will never leave." Treating
  those still-active customers as successes rather than as
  right-censored (unknown, but at-least-this-long) observations
  systematically overstates retention. This is also exactly where
  survivorship bias creeps into a loyalty metric: if you compute average
  tenure or lifetime value only over customers who are still around to
  measure, you've silently excluded everyone who already left, which
  biases the number upward — the customers who churned early are
  missing from the average precisely because they churned. A
  Kaplan-Meier retention curve (built to handle censoring correctly) or
  a competing-risks framing (a customer can leave for more than one kind
  of reason) is the honest tool; a simple average tenure computed over
  currently-active customers is not.

- **Structural breaks — test for one, don't assume smoothness.** A
  three-year series that includes a major scripted event (a competitor's
  entry, say) should not be modeled as one smooth trend running through
  it. Test explicitly for a break at the event date (a Chow test, or
  simply comparing the fitted trend before and after the date) rather
  than fitting a single line across the whole horizon and being
  surprised when the residuals look wrong around the middle. Once a
  break is confirmed, decompose *who* specifically changed behavior —
  in this model, the documented mechanism is that departure is
  concentrated among price-sensitive, less-rooted customers, which is a
  compositional shift in *who* remains, not a shift in what any
  individual customer wants.

- **A scheduled response is not an independent event.** If the owner's
  own reaction to a shock (loosening a markdown trigger, say) is itself
  scheduled to occur a fixed number of days after the shock, then any
  analysis that treats the response as its own separate, independently-
  timed event will either double-count the shock's effect or mask it,
  because the two are mechanically linked rather than coincidentally
  correlated.

- **Forecast survival — a genuine holdout, not a fitted line.** Fit a
  model on the earlier portion of the three-year horizon and evaluate it
  honestly against the later portion it never saw, rather than fitting
  across the whole series and calling the in-sample fit "validated." If
  a regime change (a competitor's entry, a rent step) occurs inside the
  held-out period, expect — and explicitly separate — two different
  kinds of forecast failure: ordinary model error (the model was simply
  imprecise) versus a real regime break the model had no way to
  anticipate (the world itself changed under it). Conflating the two
  will make a perfectly reasonable model look worse than it is, or a
  genuinely brittle one look better.

- **Capital decisions — full-life capital budgeting, not one year's
  bottom line.** An expansion or a lease renewal has to be judged over
  its whole useful life: every euro of capital actually spent, every
  euro of incremental revenue actually recovered, discounted or at
  least summed honestly over time — not by looking at whichever single
  year the decision happens to land in. This matters specifically
  because a perfectly reasonable investment, made with everything the
  owner could have known at the time, can still look bad in exactly the
  year an unrelated, later shock also arrives; judging the *decision* by
  that year's bottom line conflates two separate things (was the choice
  reasonable ex ante, and did an unrelated event also happen to hurt
  that year) that a full-life accounting keeps properly apart.

- **Always cross-check against a twin, if one exists.** Where a matched
  scenario arm with the same edit removed is available (a "no
  expansion" or "no competitor" twin), treat your own capital-budgeting
  or cost estimate as a hypothesis and the twin difference as the exact
  answer to check it against, using the same discipline as Layer 5.
