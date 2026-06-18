# 0050 — Table-row cohesion (NEGATIVE, not shipped)

- **Date:** 2026-06-18
- **Tag:** (uncommitted experiment; repo stays at 5d94136)
- **Status:** abandoned — net-negative on real general docs.

## Hypothesis (found by analyzing the table dataset, our worst at F1 0.388)

The table/dev set has 2 docs (noise), but the league-standings doc
(exetercity-mad.co.uk/snapshot) showed a real bug: 24 structurally-identical data rows,
of which the classifier keeps only 5 (rows 1,2,3,4,10) and drops the other 19 essentially
at random. Gold keeps all 24. Hypothesis: rows of one `<table>` should be classified
together — if several are kept, keep them all ("row cohesion").

## What changed (prototype, never committed)

Post-process after `model.apply`: group row paragraphs (`tr` in dom_path) by their parent
`table[N]` (xpath prefix). For a table with ≥`min_rows` data rows where ≥`min_kept` are
already kept and the kept fraction ≥`frac`, promote all data rows to good. Two variants:
1. **Blanket** (link-density gate only).
2. **Digit-gated** (only rows with ≥25% digits — target numeric data tables, skip prose
   layout tables).

## Results

| variant | general F1/Lev | table F1 | code F1 |
|---|--:|--:|--:|
| baseline | **0.8850 / 0.8205** | 0.3884 | 0.8497 |
| blanket (5,3,0.15) | 0.8820 / 0.8161 (**−0.0030**) | 0.4033 | 0.8481 (−0.0016) |
| digit-gated | 0.8850 / 0.8205 (flat) | 0.3992 | — |

- **Blanket**: regresses general −0.0030 and code −0.0016 (fires on layout/content tables
  the gold trims) for a +0.015 table gain (2-doc noise). Clear loss.
- **Digit-gated**: general *aggregate* flat, but it touches 19/1000 general docs and **all
  19 are net-negative** (worst −0.027: fitness.com, dailytech, designnews, cisco spec/stat
  tables) — keeping numeric rows the gold correctly drops. Zero general upside; the flat
  aggregate just dilutes 19 small regressions. And it didn't even fire on the Exeter league
  table it was built for (fired on the property-detail doc instead, +0.022).

## Insights

- Per-row classification is **net-correct** on general; forcing table-row cohesion trades
  19 real-doc regressions for a 2-doc-noise table gain. Fails the data-quality bar
  ("ship at Δ≈0 only if nothing real regresses" — [[data-quality-counts-without-metrics]]).
- The table dataset's low score is **gold/content-selection-limited**, not a jusText bug:
  - doc 0 (discovernorthcounty property): we select the wrong block (area-chooser nav
    list) instead of the property-detail table — a selection problem, not a row problem.
  - doc 1 (exeter league table): we extract the right rows but the gold uses U+202F cell
    separators + `  \n` row breaks (teacher typography, not in source) — unreplicable,
    same systematic gold-typography wall as U+2011/U+202F seen on forum dates.

## Next

- None on tables. Confirms the productive clean-patch frontier remains exhausted; the
  residual gap is gold-limited ([[gold-underextracts]]).
