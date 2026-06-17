# 0009 — Internals: stop fragmenting table rows & lists (ceiling-raiser)

- **Date:** 2026-06-17
- **Tag:** `0009-row-merge` (vs `0004-dom-features`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — **first lever to raise the oracle ceiling.** Shipped.

## Hypothesis (from reading jusText internals)

`ParagraphMaker` put `td, th, li, dd, dt, option, caption` in `PARAGRAPH_TAGS`, so
**every table cell and list item became its own paragraph.** A `<tr><td>Bedrooms</td>
<td>4</td></tr>` split into two paragraphs the classifier then dropped piecemeal — and
even if kept, joined by `\n\n` instead of forming the row `Bedrooms 4`. This (a) caps
the *oracle* (perfect selection still can't reproduce gold's rows/lists) and (b) wrecks
char-level formatting (Levenshtein). **Questioning this design decision:** cells/items
should stay inside their row/list paragraph.

## What changed (`justext/core.py`)

Moved `{td, th, li, dd, dt, option, caption}` out of `PARAGRAPH_TAGS` into a new
`SEPARATOR_TAGS`: they no longer break the paragraph but insert a **space**, so a `<tr>`
becomes one row and a `<ul>` one block. Retrained the general model on the new
segmentation.

## Results

**Oracle ceiling raised** (general/dev): F1 0.893 → **0.902**, Lev 0.822 → **0.838**;
table Lev 0.58 → 0.69. First change all session to move the ceiling.

Model (vs `0004`):

| dataset/split | F1 | Lev |
|---|--:|--:|
| general/dev | 0.847 → **0.849** | 0.770 → **0.772** |
| general/train | 0.850 → **0.852** | 0.774 → **0.777** |
| **table/dev** | 0.209 → **0.449** (+0.24) | (rows now formed) |
| math/dev | 0.811 → **0.826** (+0.015) | — |
| code/dev | 0.814 → 0.816 | — |
| science/dev | 0.970 → 0.965 (3-doc noise) | — |

Runtime unchanged (~9 ms/doc train). Big `table` win; general edges up (the model
captures only part of the new headroom — oracle rose +0.009, model +0.002).

## Insights

- **The segmentation was a real ceiling-setter** — every prior lever fought the model;
  this one moved the *ceiling*. Confirms the value of interrogating jusText's internals.
- General gain is small because the model still under-exploits the headroom — but the
  raised oracle (0.902/0.838) means there's now genuine room above 0.85.

## Next

- The 0002 length thresholds were tuned for the OLD (fragmented) segmentation; rows/
  lists are now longer paragraphs — **re-tune thresholds for the new segmentation** so
  the heuristic features (which the model leans on) fit. Likely frees more of the +0.009.
- Continue interrogating internals: preprocessing (forms removed?), link-density calc,
  the good-anchor revision logic.
