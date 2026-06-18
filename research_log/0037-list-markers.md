# 0037 — List markers for `<ol>`/`<ul>` (numbered & bulleted)

- **Date:** 2026-06-18
- **Tag:** `0037-lists`
- **Status:** landed — quality/structure win, metric-neutral, no general regression.

## Idea

User (gist example): a numbered list was flattened into a run-on, losing the `1. 2. 3.`
structure. Lists are common and **deterministic from the DOM** (unlike the 0024 bold guess):
100 gold docs use numbered lists (58 from source `<ol><li>`), 252 use bulleted. jusText made
each `<li>` a space-separated cell (0009), erasing the markers + line breaks.

Fix: `ParagraphMaker` now tracks `<ol>`/`<ul>` nesting; each `<li>` starts a new line with its
marker -- `"N. "` inside `<ol>`, `"- "` inside `<ul>` (gold uses `- ` 3178× vs `* ` 92×, so
`- ` is right). `normalize_whitespace` keeps the leading `\n` (same mechanism as the 0025
`<br>` fix). Non-list `<li>`/`<td>` cells keep the old space separator.

## Results (ftstack model)

| dataset/split | F1 | Lev |
|---|--:|--:|
| general/dev (1000) | 0.8849 → 0.8848 | 0.8191 → **0.8195** |
| gist (idx 774) | 0.832 → **0.834** (numbered list restored) | — |
| code/math/science | −0.001 to −0.002 (2–3 doc noise) | — |

Metric-neutral on general (slight Lev up), real list structure recovered. 61 tests pass.
gold bullet convention confirmed `- `. The domain dips are 2–3-doc-split noise.

## Note

The gist's *other* issue — code newlines — is separate: gist code in `<pre>` is handled by
0021; if a gist renders code outside `<pre>` (line-per-div), that's the roseindia-style
`\n` vs `\n\n` join, still open. List half done here.
