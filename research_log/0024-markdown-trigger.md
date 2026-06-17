# 0024 — Markdown trigger classifier (tested NEGATIVE)

- **Date:** 2026-06-17
- **Tag:** `0024-bold-trigger` (not shipped)
- **Status:** negative result — no reliable signal. Kept plain output.

## Idea (user)

Blanket markdown emission regresses (0010; this session: heading-bold −0.0018 Lev,
inline-bold −0.0020 Lev) because it markdownifies docs/spans the gold leaves plain. Learn a
cheap classifier to decide *when* to bold — per-doc or per-span — to capture the helpful
subset without the regression.

## Experiments

Inline-bold = wrap source `<strong>`/`<b>` spans (that occur in kept text) in `**`.
68% of gold bold spans match source emphasis — so recall exists — but:

- **Per-doc** (`exp_bold_trigger.py`, RF on 10 doc features): only **13%** of docs-with-spans
  are "bold-safe" (bolding doesn't lower Lev). RF learns to **never bold** (0/1000 dev docs)
  → exactly the plain baseline, Δ 0.0000/0.0000.
- **Per-span** (`exp_bold_span.py`, RF on 10 span+doc features, 9.6k train spans, gold-bold
  rate 10%): at every probability threshold 0.5–0.9 the RF bolds **0 spans** — no span
  reaches 50% confidence. Δ 0.0000/0.0000. Top features are doc-level (`doc_words`,
  `doc_density`), i.e. no per-span signal.

## Why it fails

The gold's bolding is sparse (7–10% base rate) and not separable from the 87–90% it leaves
plain by any feature available at inference. The teacher's `**` choices look close to
annotator noise w.r.t. the source structure. Combined with the hard ceiling (all markdown
markup = **+0.006 Lev** max, strip test), there is no viable metric lever here.

## Verdict

Correctly motivated, cleanly tested, **negative**. The safe choice the classifier itself
converges on — *don't markdownify* — is already what we ship. No code change. Scripts kept
under `benchmark/eval/exp_bold_*.py` for reproducibility.
