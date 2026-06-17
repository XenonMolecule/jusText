# 0006 — Failure taxonomy tool + ceiling analysis

- **Date:** 2026-06-17
- **Tag:** (analysis + new tool, vs `0004-dom-features`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — progress is *understanding*, not an F1 bump (by design)

## Why this cycle

The classifier plateaued (0003–0005). Instead of more model tuning, built a tool to
answer: **of the remaining gap, how much is fixable vs. structural vs. gold noise?**

## What changed

`benchmark/eval/ceiling.py` (new, reusable): re-runs jusText to recover *all*
paragraphs, computes the per-doc **paragraph-selection oracle** (keep paragraphs whose
tokens are ≥0.6 in gold), and classifies every doc:

| bucket | n (general/dev) | model F1 | oracle F1 | fixable headroom |
|---|--:|--:|--:|--:|
| OK (model ≈ oracle) | 812 (81%) | 0.921 | 0.934 | +0.019 |
| **MODEL_LIMITED** (oracle high, model worse) | 98 (9.8%) | 0.597 | 0.910 | **+0.031** |
| METHOD_LIMITED (oracle < 0.7) | 88 (8.8%) | 0.463 | 0.519 | +0.006 |
| GOLD_NOISE (teacher meta-commentary) | 2 (0.2%) | 0.001 | 0.000 | 0 |

Mean model F1 0.847, mean oracle 0.893, **ceiling gap 0.046**.

## Insights (the honest picture)

- **Gold noise is real but tiny.** Some golds are the 8B teacher's *reasoning* rather
  than extracted text ("The user wants to extract…", "The HTML appears to be…"). Only
  ~0.2% — not the bottleneck, but worth filtering for a cleaner benchmark later.
- **METHOD_LIMITED (8.8%) is mostly gold-limited**, not fixable by us: even perfect
  paragraph selection scores 0.52 — the gold reformats/rewrites in ways paragraph
  selection can't reproduce. Only +0.006 is reachable here.
- **MODEL_LIMITED (+0.031) is the only real headroom — and it's DIFFUSE.** Model
  *collapse* (F1<0.2, e.g. an Italian or RFC page) is just 3 of 98 docs; the rest are
  moderate per-paragraph mistakes with no single pattern. No silver bullet.
- **Conclusion:** ~0.85 F1 is near the practical ceiling of *paragraph selection* on
  this gold (oracle 0.893; gold-noise + method limits eat most of the rest). Beating it
  substantially needs a different paradigm (semantic/generative extraction like the
  teacher) — which collides with the CPU-only, ~ms/doc constraint.

## Next (options to put to the user)

1. **Consolidate**: 0.762→0.847 F1 / 0.682→0.770 Lev is a strong, fast, CPU-only result.
   Make the learned model the shipped default and validate on test once.
2. **Targeted gains** (small, in-budget): per-domain models (code/math), a multilingual
   stoplist for the rare language collapses, table flattening for the `table` set.
3. **Fairer benchmark**: filter teacher-noise gold (the `ceiling.py` GOLD_NOISE detector).
4. **Different paradigm** for >0.90 — out of the current runtime budget.
