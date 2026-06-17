# 0023 — Double-encoded HTML entity decode

- **Date:** 2026-06-17
- **Tag:** `0023-entities`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — data-quality win, zero metric regression.

## Idea

Scanning general/dev output for systematic defects found **7/1000 docs with literal HTML
entities** (`&amp;`, `&quot;`, `&gt;`, `&#160;`, `&deg;`) — vs the gold which has them all
decoded. Cause: **double-encoding** in the source (`&amp;amp;`); lxml decodes once during
parse, leaving one level behind. Fix: a second `unescape` pass on the extracted text,
under the existing `fix_encoding` flag.

Applied to the **output text** (not the input) — unescaping input could re-inject markup
(`&lt;script&gt;` → a real tag). Gated by an entity regex and **skipped for verbatim/code
paragraphs**, where an entity may be shown intentionally.

## Results

- 7/1000 dev docs changed, **0 regressed** (gated `unescape` simulation over the run).
- End-to-end: 4 docs fully cleared, scores improve or hold; 2 residual entities are inside
  code paragraphs (intentionally preserved).
- Full-mean effect: F1 +0.00002, Lev +0.00003 (negligible aggregate, real per-doc fix).
- 61/61 unit tests pass.

## Verdict

Clean quality win, zero regression — shipped alongside the 0022 mojibake repair under one
`fix_encoding` flag. Both are gated source-text repairs.

## Next

- **Markdown trigger classifier** (user idea): blanket markdown emission regresses
  (0010 + this session's -0.0018 Lev on heading-bold), because plain docs get markdownified
  wrongly. Learn a per-doc / per-heading predictor (cheap RF, <5 ms) for *when* to bold a
  heading or split a list. Could convert the regression into a net win. Planned cycle 0024.
