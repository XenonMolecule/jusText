# 0052 — Code/data-table newline join (NEGATIVE, reverted)

- **Date:** 2026-06-18
- **Tag:** `0052-block-merge` (experiment; reverted — repo stays at 72dcdaf / 0051)
- **Status:** abandoned — no upside, one real regression.

## Hypothesis (queued: "code-line join")

Code/data laid out one line per `<tr>`/`<div>`/`<p>` is emitted as one paragraph per line and
joined by the caller's `\n\n` separator, while the gold renders the block with single `\n`.
Confirmed the gold shape: the exetercity standings table is ONE block in gold (1 `\n\n`, 26
single-`\n` row separators); gist code is one block with single `\n`. So: merge a kept
uniform data table's rows (0051) into one paragraph joined by `\n`.

## What changed (reverted)

In `merge_uniform_table_rows`, after promoting a uniform table, concatenated its rows into the
first row's paragraph joined by `\n` and dropped the rest.

## Results (0052-block-merge vs 0051 promote-only, all datasets dev)

| dataset | F1 | Lev |
|---|--:|--:|
| general | 0.8852 → **0.8850** (−0.0002) | 0.8206 → 0.8205 |
| table   | 0.7101 (flat) | 0.4025 → 0.4024 (flat) |
| code/math/science | flat | flat |

Net: **no gain, one −0.13 regression.**

## Why it failed

- **No Lev upside on the target doc.** Exeter table Lev stays 0.633: the gold separates
  *cells* with U+202F (narrow no-break space) and we use a regular space — ~430 cell-boundary
  mismatches dominate the edit distance, swamping the 24-char row-separator fix. That U+202F
  is the same unreplicable teacher typography documented in 0050/[[gold-underextracts]].
- **gist doesn't qualify** — its code lines vary too much in length (CV > 0.4), so 0051
  doesn't fire and there's nothing to merge. (Gist also loses indentation upstream because
  the lines aren't verbatim; a real fix would need indentation recovery, out of scope.)
- **One real regression:** peakbagger.com 0.951 → **0.819 (−0.13)**. Merging the rows into a
  single block changed how the dedup pass sees them — as separate row-paragraphs the
  near-duplicate rows are correctly deduped; as one block they are not (or vice-versa),
  shifting tokens. The interaction with `_dedup_kept` is the killer.
- **roseindia** (the other queued example) is dominated by related-Q&A over-extraction
  (a Q&A/content-selection problem), not the newline join — out of scope for this fix.

## Insight

Row promotion (0051) is the safe, valuable part; **re-joining** rows into a block is not —
it has no metric upside here (gold cell-typography) and perturbs dedup. Leave kept table rows
as separate paragraphs. The "code newline join" queue item is closed: the tractable win
(keep the rows) already shipped in 0051; the formatting half is gold-typography-limited.
