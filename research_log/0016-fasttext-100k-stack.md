# 0016 — fastText-on-100k stack (BREAKTHROUGH: best model)

- **Date:** 2026-06-17
- **Tag:** `0016-ftstack`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — **new best model.** Shipped as `general-ftstack.joblib` (opt-in,
  needs the fastText `.bin`); fast snapshot remains the portable default.

## What changed

The user supplied **100k docs** (`benchmark/big_train.jsonl.gz`) — 10× the train set.
Trained a **fastText** char/word-ngram classifier on its ~9.1M paragraphs (fuzzy label;
user's recipe: epoch 5, lr 0.1, dim 100, bigrams, softmax, min-count 500), and **stacked
its keep-probability into the struct RF** (40×d14) on top of the 0009 segmentation +
`<pre>` rule. `ParagraphClassifier` now supports a fastText text model
(`fasttext_path` in the payload); `train_classifier.py --fasttext-model`.

## Why it works (the bet paid off)

The deep dives (0012, 0015) showed the residual gap is **context-dependent boilerplate**
(forum timestamps vs article datelines) — not rule-separable, needs a text model with
enough data to learn the patterns. fastText text-only scaled with data:
**0.799 (10k) → 0.828 (100k)**, and stacking the 100k model cleared the prior ceiling.

## Results (vs fast snapshot 0.852/0.776)

| dataset/split | F1 | Lev |
|---|--:|--:|
| **general/dev** | 0.852 → **0.870** | 0.776 → **0.801** |
| **general/train** | 0.852 → **0.873** | 0.778 → **0.805** |
| code/dev | 0.830 → 0.832 | — |
| science/dev | 0.965 → **0.982** | — |
| table/dev | 0.449 → **0.507** | — |
| math/dev | 0.826 → 0.803 (2-doc noise) | — |

**train ≈ dev → not overfit.** Unlike the 0013 sklearn stack (which regressed domains),
the 100k fastText model *generalizes* — it lifts science and table too. Runtime **~20
ms/doc** (3 workers; fastText loads per worker), within the 50-60 ms budget.

**Gap to target now: F1 0.030, Lev 0.049** (was 0.090/0.094 at baseline).

## Artifacts / reproducibility

- `models/general-ftstack.joblib` (RF + fastText ref) — committed (8.5 MB).
- `models/general_ft.bin` (807 MB fastText) — **gitignored**; regenerate:
  `python benchmark/eval/train_classifier.py` extracts paragraphs; fastText trained on
  `big_train.jsonl.gz` paragraph (text→fuzzy-label) with the recipe above.
- `models/general-fast.joblib` — the fast snapshot (0.852, 9 ms/doc, no fastText), the
  portable fallback.

## Next

- Train the RF stack on the **full 100k struct** (not just 10k) — may add more.
- Tune the fastText recipe / a 2nd-pass; threshold-tune the stack.
- Per-domain check now that domains improved (esp. forum pages, the known hard set).
