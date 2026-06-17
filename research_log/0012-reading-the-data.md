# 0012 — Reading the data (observations) + fuzzy label + <pre> rule

- **Date:** 2026-06-17
- **Tag:** `0012-pre-rule` (vs `0009-row-merge`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — shipped the `<pre>` rule; documented observations + fuzzy label.

Spent this cycle **reading actual extractions vs gold** (diff tools) and the HTML, per
the highest-leverage suggestion. Findings:

## Observations (what's actually off, and why)

1. **Gold noise is tiny (0.3%).** A few golds are the 8B teacher's *reasoning/abstention*
   ("The user wants to extract…", "</s> The final answer is…", "The HTML appears to be…").
   F1≈0, unfixable, but only 3 docs — costs ~0.003. Not the lever.
2. **Gold is markdown (49% of docs):** `**bold**` headers, `- `/`1.` lists, ```` ``` ````
   code fences, `---` rules. jusText emits plain text. BUT the markers are ~14 chars per
   doc — stripping them from both sides moves the score +0.0001 F1 / +0.002 Lev. **Like
   dashes/whitespace before: prevalent but too few chars to matter.** Cosmetic ≠ lever.
3. **The real gap is content *selection*, and it's diffuse.** Boilerplate that leaks:
   image captions/credits ("The Associated Press"), "javascript disabled" notices,
   donation banners, social-share ("Like this"), blog footers, comment timestamps
   ("GarethNov 13 '10"). Content jusText *misses* by picking the **wrong region**:
   `iheart` kept "Lyrics/Chat" nav and missed the artist bio; `datatracker` kept the IESG
   sidebar and missed the RFC body; `mcmua` kept the homepage welcome, missed the awards.
4. **Some "over-extracts" are teaser-length gold** — the teacher kept only title+byline+
   intro while jusText returns the full article (ratio 20-33×). A gold quirk.

## Fuzzy-alignment label (key insight)

Labelling a paragraph "keep" by **`rapidfuzz.partial_ratio(paragraph, gold) ≥ 85`**
(is it actually *in* the gold) instead of token-overlap lifts the **oracle 0.902 → 0.944
F1 / 0.838 → 0.906 Lev** — *above target*. The ceiling is reachable in principle. But:
- The **struct RF trained on the fuzzy label is worse** (0.849→0.832): the label is
  correct yet hard to predict from structural features, so the model just gets timid.
- A **text-model stack trained on the fuzzy label** (char-ngram hashing → logistic,
  stacked into the RF) reaches **0.853 F1 / 0.781 Lev at ~29 ms/doc** — best combo, Lev
  +0.009. Documented as a config (now in budget); not yet shipped (build cost).

## Shipped this cycle: `<pre>` keep rule

From reading: RFC/code/ASCII content lives in `<pre>` (low stopword density → wrongly
dropped). **Force-keep paragraphs inside `<pre>`** (preformatted = intentional content),
in `ParagraphClassifier.apply`. Domain-agnostic, safe:

| dataset/split | F1 | Lev |
|---|--:|--:|
| general/dev | 0.849 → **0.852** | 0.772 → **0.776** |
| general/train | 0.852 → **0.852** | 0.774 → **0.778** |
| code/dev | 0.816 → **0.830** (+0.014) | 0.686 → **0.708** |
| math, science | unchanged (no `<pre>`) | — |

## Next

- **Ship the fuzzy text-stack** (now within the 50-60 ms budget) — best F1/Lev; combine
  with the `<pre>` rule. Then a stronger text model on the fuzzy label is the path to
  push the model toward the 0.944 oracle.
- Targeted boilerplate features for the recurring leaks (image credits, JS notices).
