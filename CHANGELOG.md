# Changelog

All notable changes to `grocery-sim` are documented here.

## 0.1.6 — 2026-07-20

### Package

- `describe()` now classifies each run's engagement brief along a
  `diagnose` / `optimize` / `invest` axis, on top of the existing
  struggling/thriving/uncertain read. An elevated shrinkage rate
  (write-offs priced at cost, as a share of revenue) reframes the ask
  as tightening operations rather than chasing a single villain; a
  thriving shop sitting on real unspent retained earnings on the
  three-year horizon reframes it as a capital decision instead of a
  diagnosis.
- The letter now folds the per-year interview beats into one condensed
  paragraph, so a reader of the letter alone gets the shape of what
  happened across the run without reading the full interview.
- The letter's closing lines now include an honest records-caveat
  clause and a closing ask ("Tell me what the numbers actually say"),
  so it reads as a complete letter on its own.

### Project site

- Split the single `malm-market` exemplar analysis into three focused
  pages: a case description (the client brief), a stakeholder report
  (plain-language answers, in the client's own question order), and a
  technical report (GLM, gradient boosting, and hierarchical Bayesian
  inference, stated in full with McElreath-style generative notation).
- Added a generated-briefs page showing real `optimize`/`invest`
  engagement briefs produced by the `describe()` changes above.
- Fixed a chart-overflow bug present since the interactive figures
  were first embedded: Plotly's HTML export wraps each chart in a
  container with a hardcoded pixel width (920–980px), wider than the
  site's 900px content column. All figures and the two chart-generation
  scripts now use 860px so charts sit inside the page with margin to
  spare.
