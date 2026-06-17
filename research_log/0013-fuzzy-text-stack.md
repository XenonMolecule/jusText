# 0013 — Fuzzy text-stack (built; best general; not defaulted)

- **Date:** 2026-06-17
- **Tag:** `0013-fuzzy-stack` (vs `0012-pre-rule`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — capability shipped; **balanced model kept as default** pending sign-off.

## What was built

Implemented the stacked text model end-to-end (the 0012 "next"):
- `ParagraphClassifier` now optionally holds a `text_vectorizer` + `text_model`; at
  inference it appends the text keep-probability as a feature before the struct RF.
- `train_classifier.py --stack --label fuzzy`: trains a char-`wb` 3–5gram HashingVectorizer
  (2^19) + SGD-logistic on the fuzzy label, stacks its prob into the RF (40×d14).

## Results (general/dev + train, with the <pre> rule on top)

| config | gen dev F1/Lev | gen train F1/Lev | ms/doc | model |
|---|---|---|--:|--:|
| 0012 balanced (shipped) | 0.852 / 0.776 | 0.852 / 0.778 | ~9 | 3 MB |
| **0013 fuzzy-stack** | **0.856 / 0.781** | **0.864 / 0.792** | ~17 | 12 MB |

Best general numbers of the project (train +0.011 F1 / +0.015 Lev; dev +0.004 / +0.006).

Domain dev (tiny, noisy): code 0.830→0.828 (tie), math 0.826→0.750, science 0.965→0.936,
table 0.449→0.355. The non-code drops are on 2–3-doc splits (noise-level), but the text
model is trained only on general, so some OOD degradation is plausible.

## Decision

**Kept the balanced pre-rule model as default** (`--label overlap`, no stack): better on
4/5 datasets, 3 MB, ~9 ms. The fuzzy-stack's general gain is small (+0.004 dev) and its
costs (12 MB model, ~2× runtime, possible domain OOD) plus the unverifiable domain dev
(tiny splits) make defaulting it a call for the user, not an autonomous one. It is fully
built and one flag away: `train_classifier.py --label fuzzy --stack`.

## Insight

The stack confirms the ceiling shape: even the best learnable combo (struct + text +
fuzzy label + <pre>) reaches ~0.856 dev / 0.864 train on general — short of 0.90. The
fuzzy *oracle* is 0.944, but no fast model predicts "is this in the teacher's output"
well enough; the residual is the teacher's semantic content judgment.

## Next (for user)

- Flip default to fuzzy-stack if the general target outweighs domain/size/runtime — or
  confirm domain impact on more data first.
- A stronger text model (word+char, or a tiny MLP) on the fuzzy label is the most likely
  remaining lever toward the 0.944 oracle.
