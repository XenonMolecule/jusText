# 0003 — Learned paragraph classifier

- **Date:** 2026-06-16
- **Tag:** `0003-learned-rf` (baseline compared against: `0002-relax-thresholds`)
- **Commit:** `10bd0e4`
- **Status:** landed

## Hypothesis

After 0002, the failure mode flipped to **classification quality**, not segmentation.
The decisive diagnostic: an **oracle that keeps jusText's own paragraphs whose tokens
are ≥60% present in gold scores F1 0.893 / Lev 0.822** — i.e. jusText's segmentation is
good enough to nearly hit the target; the entire +0.084 gap is the keep/drop *decision*.
Heuristic param-tuning plateaus at ~0.81, so: **train a small classifier on the 10k-doc
train split to replace the keep/drop decision.** Constraint: CPU-only, ~ms/doc, no large
model (a hard objective — runtime is tracked).

## What changed

- `justext/classifier.py` (new): cheap per-paragraph features (length, stopword/link
  density, heading, position, **the heuristic's own cf_class + is_boilerplate**, and
  prev/next neighbour context) + a `ParagraphClassifier` that re-decides keep/drop.
  Lazy sklearn/joblib import — jusText core stays dependency-free.
- `justext.justext(..., model=...)`: opt-in; the model runs *after* the heuristic, so it
  can only refine it. Default behaviour unchanged.
- `benchmark/eval/train_classifier.py` (new): trains a RandomForest (25×depth-12) on
  train-split paragraph features; label = token-overlap≥0.6. `run_eval.py --model`.
- Model picked by sweep: linear LR underfit (0.81); HistGBM-300 was accurate but 39
  ms/doc (too slow). RandomForest 25–40 trees hit the accuracy/speed sweet spot.
  Dropped per-char ratio features (low importance, high cost).

## Results (F1 / Lev-sim, vs `0002-relax-thresholds`)

| dataset | split | F1 | Lev |
|---|---|---|---|
| general | train | 0.809 → **0.848** (+0.038) | 0.724 → **0.771** (+0.047) |
| general | dev   | 0.809 → **0.843** (+0.034) | 0.725 → **0.766** (+0.041) |
| code    | dev   | 0.772 → 0.814 (+0.042) | 0.649 → 0.684 |
| math    | dev   | 0.719 → 0.830 (+0.111) | 0.595 → 0.740 |
| science | dev   | 0.939 → 0.970 (+0.031) | 0.889 → 0.940 |
| table   | dev   | 0.044 → 0.064 (+0.020) | 0.099 → 0.117 |

The **general** model transfers to every domain (table excepted). dev≈train → not
overfit. **Runtime:** general/train 4.8 → 8.9 ms/doc (+~4 ms; the RF `predict` call, not
features). Still single-digit ms/doc, but ~2× baseline — flagged for optimization.

## Insights

- Confirmed: the gap was classification, and a tiny model captures ~40% of the oracle
  headroom (0.809 → 0.845 of the 0.809 → 0.893 available).
- Top features: `cf_good`, `not_boilerplate`, `link_density`, neighbour link/length —
  the model mostly *refines the heuristic using context*, exactly as intended.
- `table` is immune: tables are classified boilerplate *before* the model ever sees a
  useful signal — needs structural table handling (own cycle).

## Next

- **0.90 cap:** even the oracle is 0.893 — paragraph selection alone tops out below the
  F1 target. To exceed, need better labels (the 0.6-overlap label is noisy) and/or
  segmentation/formatting fixes.
- Runtime: shrink/threshold the RF or export to pure-Python to get back toward baseline.
- `table`: dedicated handling. Per-domain models for code/math.
