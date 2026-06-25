# 0083 — Words glued at inline-element / block boundaries (spacing)

- **Date:** 2026-06-25
- **Tag:** `spacing-dev2` (baseline: `0082`)
- **Status:** landed — pajcisenate 0.93→0.96, dev2 flat, dev +0.0001, both Lev flat (no regression).

## Trigger

User: "several docs get spaces messed up." Two flagged docs, two distinct causes:

- **thejournal.com** `...Title II D: Enhancing<img src=...>Education Through Technology...` — an
  inline `<img>` sits between two words with no surrounding whitespace, so the text runs joined to
  `EnhancingEducation`. Gold: `Enhancing Education`.
- **pajcisenate.org** (officer directory) `<strong>Treasurer</strong></address><address>...Julia` —
  adjacent block-level `<address>` elements glued to `TreasurerJulia`, `SecretaryChuck`, etc. Gold
  puts each on its own line.

Not every glue is ours: thejournal also has `BehindAct`, `aswell`, `technologywill` glued **in the
raw source** (a print-magazine→HTML conversion artifact, no tag/space between the words). The gold
fixes those from context; we can't recover a separator that isn't in the HTML. Only the boundary
cases above are fixable.

## Why these slipped through

The SAX `ParagraphMaker` inserts a space for `SEPARATOR_TAGS` (td/th/li/dd/dt) and a `\n` for `<br>`,
and starts a new paragraph for `PARAGRAPH_TAGS`. But `<img>` and `<address>` were in **neither** set,
so they were treated as inline with no separator. The existing 0026 fix only covers a *blank text
node* between inline elements; a void `<img>` or directly-adjacent block tags have no text node, so
nothing was emitted.

## Fix

- `<img>` → `SEPARATOR_TAGS` (emit a space). An image between words is a visual gap.
- `<address>` → emit a `\n` at start (like `<br>`): a line break **within** the paragraph, not a
  paragraph split. The split (adding `address` to `PARAGRAPH_TAGS`) tested worse — it let the
  classifier drop officer rows piecemeal (pajci 0.935 vs 0.962 for the line-break form).

## Results

| variant | thejournal | pajcisenate | dev2 F1 |
|---|--:|--:|--:|
| baseline | 0.782 | 0.927 | 0.8803 |
| + img→space | 0.784 | 0.927 | 0.8803 |
| + address→line-break | 0.784 | **0.962** | (see guardrail) |

pajcisenate officer list now reads `President\nSally Traczuk #68943\n5 Forrest Lawn Court...\n...`
matching the gold. thejournal gains little (its remaining glue is unrecoverable source-level).

| set | F1 | Lev |
|---|--:|--:|
| dev2 | 0.8803 → 0.8803 (flat) | 0.8175 → 0.8175 (flat) |
| dev | 0.8912 → 0.8913 (+0.0001) | 0.8275 → 0.8275 (flat) |

The dev2/dev aggregates barely move (img/address are rare), but no doc regresses and the flagged
quality wins are real. 61 tests pass.

## Cost

Two tag-set/handler additions in the SAX pass; whitespace is normalized afterward so the extra
space/newline can never double up.
