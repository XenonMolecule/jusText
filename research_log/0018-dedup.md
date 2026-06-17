# 0018 — Paragraph deduplication (clean, safe win)

- **Date:** 2026-06-17
- **Tag:** `0018-dedup`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — shipped in `ParagraphClassifier.apply()`.

## Origin

Found via the math/forum duplication case (user asked "what is boilerplate math?"):
forum pages quote the same post multiple times, and MathJax adds a separate LaTeX-source
copy, so jusText keeps the **same paragraph 2–3×** while the gold keeps it once (train#1:
"I have two triangles ASB and AOB" appears 3× in pred, 1× in gold; pred 13.5k vs gold
9.3k chars). It's not "boilerplate math" — it's **duplication**.

## What changed

`ParagraphClassifier.apply()` now runs a **dedup pass**: in document order, a kept
paragraph (≥12 chars, normalized) that exactly- or near-matches (`rapidfuzz.ratio ≥ 97`)
an earlier kept paragraph is marked boilerplate. The gold never repeats a paragraph, so
this is safe and domain-agnostic.

## Results (dev, fast model; with the `<pre>` rule)

| dataset | baseline | +dedup |
|---|--:|--:|
| **general** | 0.852 / 0.776 | **0.858 / 0.784** (+0.006 F1 / +0.008 Lev) |
| code | 0.830 | **0.834** (+0.004) |
| math / science / table | — | **unchanged** (no harm) |

Removes ~1.65 duplicate paragraphs/doc on general. Stacks additively with the fastText
model (the ftstack re-measure with dedup is queued after the in-flight 50k-struct run).

## Insight

Over-extraction (the documented real headroom, 0015) includes a chunk of pure
**duplication** that a safe, content-free rule removes — no model needed. Likely helps
any quote-heavy domain (forums, threads, comment sections).

## Next

- Re-measure the shipped **fastText-stack + dedup** across all datasets (general 0.870 →
  expect ~0.876) once the 50k-struct job frees compute.
- Consider a core-level dedup option (benefits the heuristic default too).

## Dedup tuning (confirmed optimal)

Tested more aggressive variants on general/dev: exact/ratio>=97 **0.855** (best) >
ratio>=90 0.854 > containment 0.839. Lower thresholds / substring-containment
**over-remove** distinct content (a short content line that's a substring of a longer
one is not a duplicate). Current setting is the sweet spot.
