# 0029 — U+FFFD repair via learned context table

- **Date:** 2026-06-17
- **Tag:** `0029-fffd`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — quality fix (apostrophes/quotes/dashes), zero regression.

## Idea

88/1000 general/dev docs contain U+FFFD (3,796 chars): a cp1252/Latin-1 byte decoded as
utf-8 with `errors='replace'`. The byte is **lost**, so it's not reversible like mojibake
(0022) — but the surrounding context usually pins the original. Aligning corrupted html to
gold showed the lost chars are **not random**: 61% are `'` (apostrophe in contractions),
~30% are also `�` in the gold (leave alone), the rest curly quotes / dashes / accents.

User floated kenlm n-gram infilling. Measured trade-off: a full char-LM is overkill for the
61% apostrophe case (a lookup nails it) and **risky on foreign-name accents** (an English LM
predicts the base letter — a confident wrong fix). Shipped the lightweight equivalent: a
**data-driven (2-before, 2-after) → char table** (`_char_repair.py`, 235 high-confidence
contexts, ≥3 samples & ≥80% agreement, learned from train). Unknown context → left as `�`
(no guess). Applied to non-verbatim paragraph text under `fix_encoding`.
Rebuild: `benchmark/eval/build_char_repair.py`.

## Results (ftstack model)

| | F1 | Lev |
|---|--:|--:|
| general/dev (1000) | 0.8827 (flat) | 0.8169 (flat) |
| 88 FFFD docs only | flat | +0.0006 |
| code/math/science/table | flat | flat |

61/61 tests pass. Recovers `don�t`→`don't`, curly quotes, dashes; leaves rare proper-noun
accents (`K�ppen`) as `�` rather than mis-guessing. Aggregate is flat (too few docs) but
it's a real readability fix with **zero regression** — the data-quality bar we ship on.

## Note

The lossless fix is **upstream**: decode captured pages with proper charset (meta →
cp1252/Latin-1 fallback) instead of utf-8+replace. This table is the best in-jusText option.
