# 0020 — Combiner-on-more-data: confirmed NOT the lever (negative)

- **Date:** 2026-06-17
- **Status:** landed — negative result; confirms the ceiling.

## Test

The fastText text model is trained on the 100k (big_train); the RF combiner is trained
on 10k (general/train). Hypothesis: training the combiner on more data helps. Trained the
combiner on **50k big_train docs** (4.5M paragraphs, same 37-feature setup).

## Result — NEGATIVE

| combiner training data | dev F1 / Lev (no-pre/dedup) |
|---|---|
| 10k general/train (shipped) | **0.870 / 0.804** |
| 50k big_train | 0.859 / 0.788 |

More data made it **worse**. Reason: the 10k is **in-distribution** (general/train ~
general/dev); the 50k big_train is a broader corpus, so the combiner trained on it is
**out-of-distribution** for general/dev. The fastText *text* model generalizes from
big_train (text patterns transfer), but the RF combiner (struct + ftprob combination) is
distribution-sensitive.

## Conclusion

- The combiner is **not data-limited** (925k in-distribution paragraphs is plenty).
- This was the last untried *substantive* lever. With it ruled out, **0.880 F1 / 0.814
  Lev on general is the practical ceiling** of this fast paragraph-selection pipeline.
- The only remaining paths to 0.90/0.85: (a) more **in-distribution** fastText/training
  data, (b) a heavier content model (beyond fastText) — both require the user.

## Follow-up: fastText augmented with in-distribution general/train — also NEGATIVE

Appended the 925k general/train paragraphs to the big_train fastText training and
retrained: text-only unchanged (0.829 vs 0.828), but the **stack dropped to 0.859 vs
0.870** (no-pre). Adding the in-distribution data perturbed the fastText probs in a way
the combiner liked less. Big_train-only fastText stays best. Net: the data-augmentation
angle (both combiner-side and fastText-side) does **not** help — confirms 0.880/0.814 is
the ceiling with the current data; more *volume* of similar data won't move it.

## Follow-up 2: fastText epochs at dim100 — NEGATIVE (ep5 optimal)

Tested more training epochs at the safe dim100 (the failed sweep used dim200): ep5
text-only 0.826, ep10 0.823, ep20 0.821 — more epochs **overfit and hurt**. The user's
conservative ep5/dim100/bigrams recipe is optimal. fastText text-only is maxed ~0.828.

## FINAL: every lever exhausted

Confirmed across 0001-0020: features (struct/DOM/content/text/neighbor), combiner (RF>GBM;
10k-in-dist > 50k-OOD), fastText recipe (ep5/dim100 optimal; more epochs/dim hurt),
augmentation (neg), rules (threshold/header/window/math-LaTeX/formatting = washes),
smoothing (neg). Shipped wins: 0002 thresholds, 0003 RF, 0009 segmentation, 0012 <pre>,
0016 fastText-100k, 0018 dedup, 0019 neighbor-prob. **0.880 F1 / 0.814 Lev on general is
the definitive practical ceiling of fast CPU paragraph-selection on this gold.** Closing
the last 0.020/0.036 needs a heavier (e.g. generative) model or a materially different
data distribution — both outside the fast-extraction paradigm.

## Follow-up 3: per-doc adaptive threshold — NEGATIVE

Tested per-document thresholds (Otsu on the doc's prob distribution; mean+0.25std) vs
global 0.5: Otsu 0.874, mean+std 0.873 vs **global 0.5 = 0.878**. The RF probs are
globally well-calibrated; per-doc thresholds add noise (distributions aren't cleanly
bimodal). Global 0.5 stays. Yet another confirmed dead-end — the ceiling holds.
