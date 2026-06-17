# 0019 — Neighbour fastText-prob features (boundary signal)

- **Date:** 2026-06-17
- **Tag:** `0019-nbr`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — new best. Shipped in the ftstack model + classifier.

## Idea

The fastText keep-prob is the strongest signal, but the RF combiner only saw *struct*
context of neighbours, not their keep-probs. Content is contiguous, so a paragraph's
**previous/next fastText keep-prob** is a strong block-boundary signal. Added
`prev_ftprob`, `next_ftprob` (within each doc, 0-padded at edges) to the stacked feature
vector (now 37 features). Updated both `predict_keep` and `train_classifier`.

## Results (vs prior best ftstack+dedup 0.876/0.808)

| dataset/split | F1 | Lev |
|---|--:|--:|
| **general/dev** | 0.876 → **0.880** | 0.808 → **0.814** |
| **general/train** | 0.877 → **0.880** | 0.811 → **0.816** |
| math/dev | 0.806 → **0.828** (+0.022) | — |
| science/dev | 0.982 → **0.989** | — |
| code/dev | 0.837 (flat) | — |
| table/dev | 0.507 → 0.399 (−0.108) | — |

train ≈ dev → not overfit. General (primary target), math, science up; code flat. **Gap
to target now 0.020 F1 / 0.036 Lev** on general (from 0.138/0.168 at baseline).

## Caveat

`table/dev` regressed (−0.108) — but it's a **2-doc split** (noise-level). Plausible
mechanism: neighbour smoothing hurts tables where adjacent rows have independent
keep-status. Flagged; revisit if a larger table set is available. Net clearly positive
on the reliable signals (general 1000 docs, math/science up).

## Next

- The Lev gap (0.036) is now the larger one; it's content-selection-limited (formatting
  gives ≤+0.009). Remaining levers: more fastText data, or precision refinements.
- Consider guarding the neighbour feature for table-like docs if a real regression.
