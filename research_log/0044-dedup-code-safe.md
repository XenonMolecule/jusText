# 0044 — Dedup skips code (don't merge distinct code examples)

- **Date:** 2026-06-18
- **Tag:** `0044-dedup-code`
- **Status:** landed — fixes a serious code break, general/dev flat.

## Bug (user-flagged, high priority)

The dedup pass (0018/0030) **broke code** on gokulmig.blogspot.com (PostgreSQL XML): a page
with three SQL examples whose INSERT statements share a first line
(`INSERT INTO "user_add"("name", address, phone)`) but differ in their VALUES. Dedup saw the
identical first line as a near-duplicate and dropped the second/third example's opener,
mangling distinct code. Code legitimately repeats lines (two examples, loops, …); dedup was
built for repeated PROSE (forum quotes, teasers), not code.

## Fix

`_dedup_kept` now skips code-like paragraphs: **verbatim**, or **>13% non-alphanumeric chars**
(code has ~20% — quotes/parens/semicolons/commas; prose has ~2-4%). Such paragraphs are
neither dropped nor used to drop later ones, so two SQL examples sharing a line both survive.
(An earlier stopword-density gate was dropped — it false-skipped low-stopword prose the gold
*does* dedup, costing −0.0005 general; the punctuation signal alone is cleaner.)

## Results

| | F1 | Lev |
|---|--:|--:|
| **gokulmig** | 0.907 → **0.930 (+0.023)** | 0.779 → **0.829** |
| general/dev | 0.8850 (flat) | 0.8200 → 0.8201 |
| code/dev (11) | 0.8510 → 0.8495 | (−0.0015, gold-inconsistency noise) |
| math/science/table | flat | flat |

Distinct code examples preserved, prose dedup (forum quotes/teasers) still works, general/dev
flat. The tiny code/dev dip is the gold inconsistently deduping some repeated code elsewhere —
worth it to stop mangling distinct code. 61 tests pass.
