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
