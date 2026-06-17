# 0005 — Decision threshold (negative) + plateau assessment

- **Date:** 2026-06-17
- **Tag:** (no model change — analysis only, vs `0004-dom-features`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed (negative result, documented to avoid re-tread)

## Hypothesis

After 0004, over-extraction dominates general/dev low scorers (213 over- vs 69
under-extractors; precision 0.61, recall 0.81). Hypothesis: **raise the classifier
decision threshold** (0.5 → higher) to trade recall for precision and lift F1.

## Result — NEGATIVE

Threshold sweep on the 0004 model (no retraining):

| threshold | dev F1 | dev Lev | train F1 |
|--:|--:|--:|--:|
| **0.5** | **0.847** | **0.770** | **0.850** |
| 0.6 | 0.835 | 0.760 | 0.844 |
| 0.7 | 0.812 | 0.734 | 0.824 |

0.5 is already optimal — F1 falls monotonically as the threshold rises. Over-extraction
is **doc-specific** (some docs leak boilerplate while others under-extract), so a single
global threshold can't fix it; raising it loses more on under-extracted docs than it
gains. Kept threshold = 0.5.

## Insights — the classifier has plateaued

Across 0003–0005 the learned classifier sits at **~0.847 F1 / 0.770 Lev** on general,
and three independent levers failed to move it:
- stricter labels (0004) — model-limited, not label-limited;
- richer DOM features (0004) — only +0.004;
- decision threshold (0005) — 0.5 already optimal.

The model captures most of its 0.6-oracle (0.893); the remaining gap needs **better
per-paragraph discrimination or different inputs**, not more tuning of the current setup.

`has_table` docs still lag (general: 0.827 vs 0.865 non-table).

## Next (bigger swings — likely need one to break 0.90/0.85)

1. **Richer cheap features**: boilerplate-phrase / char-class signals to separate the
   doc-specific leaks the current features miss.
2. **Stronger model** (small GBM) — only if it stays ~ms/doc.
3. **Segmentation / table flattening**: change the *inputs* (raises the oracle itself).
4. Accept ~0.85 as the practical ceiling of paragraph-selection on this gold and report.
