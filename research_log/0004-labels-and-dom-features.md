# 0004 — Label ceiling (negative) + DOM-structure features

- **Date:** 2026-06-17
- **Tag:** `0004-dom-features` (baseline compared against: `0003-learned-rf`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed

## Hypothesis

0003 ended capped at the oracle (0.6-overlap label → 0.893). Sweeping the label
threshold showed a **stricter label raises the oracle** (0.7 → 0.916, 0.8 → 0.926),
*above* the 0.90/0.85 target. Hypothesis: **retrain on a stricter label** to push the
classifier past 0.85.

## What changed / what we found

1. **Label sweep (NEGATIVE result).** Retraining on overlap 0.7/0.75/0.8 did **not**
   help the model — dev F1 stayed flat (0.843) and *dropped* at 0.8 (0.836). The
   oracle improves with gold, but the model can't exploit it: **the bottleneck is
   feature discrimination, not the label.** Kept label = 0.6.
2. **DOM-structure features (pivot, small win).** jusText paragraphs carry a
   `dom_path` we'd never used. Added cheap features from it: tree depth + membership
   of nav/aside/header/footer/form/list/table/main/blockquote. (`justext/classifier.py`.)

## Results (F1 / Lev-sim, vs `0003-learned-rf`)

| dataset | split | F1 | Lev |
|---|---|---|---|
| general | dev   | 0.843 → **0.847** (+0.004) | 0.766 → **0.770** |
| general | train | 0.848 → **0.850** (+0.002) | 0.771 → **0.774** |
| table   | dev   | 0.064 → **0.209** (+0.145) | — |
| code/science | dev | ~flat | — |

Runtime unchanged (general/train ~9 ms/doc). The standout is **`table` +0.145**: the
`dom_table` feature lets the model keep tabular content the heuristic kills.

## Insights

- **The classifier has plateaued ~0.847** on general. Refining features over jusText's
  existing paragraphs yields diminishing returns; we're ~0.046 below even the 0.6 oracle
  and the model can't close it with these features.
- DOM location is a genuine signal (esp. for tables) but small for general overall.
- To break 0.90/0.85 we likely need to change the **inputs**, not the classifier:
  better segmentation, table flattening, and/or richer content features.

## Next

- **Tables**: the `dom_table` win suggests dedicated table flattening could take the
  `table` set from 0.2 → much higher, and helps general's table-heavy docs.
- Consider a stronger model (small GBM) only if runtime stays ~ms/doc.
- Investigate the Lev gap (0.77 vs 0.85 target) — likely formatting/segmentation.
