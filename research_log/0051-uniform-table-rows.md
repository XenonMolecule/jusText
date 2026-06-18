# 0051 — Keep whole uniform data tables (row cohesion, done right)

- **Date:** 2026-06-18
- **Tag:** `0051-table-merge`  (baseline: 5d94136 / 0049)
- **Status:** landed — table +0.32, general net-positive.

## Hypothesis (user-flagged)

The learned classifier scores each table row independently. On a long standings/stats/spec
table — rows that are short and near-identical — it keeps a few rows and drops structurally
identical siblings **at random** (exetercity-mad league table: kept 5 of 24 rows; gold keeps
all 24). User: "we can't be dropping rows randomly, that would be exceedingly bad." When a
table is uniform data, keeping some rows and dropping others is self-evidently inconsistent —
keep them all.

## What changed

`merge_uniform_table_rows(paragraphs)` (core.py), run after classification (model or
heuristic). Groups row paragraphs by their innermost `table[N]` xpath; promotes ALL rows of a
table to `good` when:
- ≥8 rows that aren't link-heavy (`links_density < 0.6` — excludes nav tables; team-name
  hyperlinks in data rows sit ~0.2 so 0.6 keeps them),
- ≥2 rows already kept (the table holds real content),
- rows are **uniform**: length coefficient-of-variation ≤0.4 **and** median row length ≤160
  chars (data cells, not the long high-variance rows of a forum/layout table).

This is the discriminator the earlier attempts (0050) missed: 0050 gated on digit-ratio /
page-dominance and fired on forum/layout tables (regressed general). Uniformity + short cells
cleanly separates data tables from forum post-tables.

## Results (sweep, prototype harness)

| config | general F1 | table F1 | touched(gen) | net on touched |
|---|--:|--:|--:|--:|
| baseline | 0.8850 | 0.3884 | — | — |
| **A (cv≤0.4, med≤160)** | **0.8852** | **0.7101** | 8 | **+0.158** |
| B (cv≤0.3, med≤120) | 0.8851 | 0.7101 | 6 | +0.108 |
| C (cv≤0.5, med≤200) | 0.8852 | 0.7101 | 10 | +0.144 |

Shipped **config A**. Both table docs fire (exeter +0.622 → ~0.97; discovernorthcounty
property +0.022). On general it touches 8 docs, **net +0.158** (almost all positive — it
keeps data-table rows the gold also keeps), single worst −0.007.

**Official run_eval, all datasets dev (vs clean baseline `baseline-pre0051`, same model):**

| dataset | F1 base→new | Lev base→new |
|---|--:|--:|
| general | 0.8850 → **0.8852** | 0.8205 → 0.8206 |
| code    | 0.8497 → 0.8497 (flat) | 0.7526 (flat) |
| math    | 0.8580 → 0.8580 (flat) | 0.7670 (flat) |
| science | 0.9883 → 0.9883 (flat) | 0.9751 (flat) |
| table   | 0.3884 → **0.7101** (+0.32) | 0.1676 → **0.4025** |

**Zero regression on any dataset; general up, table up +0.32.** 61 tests pass.

## Insights

- The real signal for "keep the whole table" is **row uniformity** (short, low-variance,
  many rows), not numeric-ness or page-dominance. Forum/layout tables have few, long,
  high-variance rows and are correctly left to per-row classification.
- First genuine table-dataset win and the first change to *raise* general since the plateau,
  not just hold it — because it fixes a real classifier inconsistency rather than overfitting
  the gold.

## Next

- Watch for any data table with a stray very-long row (e.g. a notes cell) that lifts the CV
  above 0.4 and suppresses the merge; median-len gate already handles the common case.
