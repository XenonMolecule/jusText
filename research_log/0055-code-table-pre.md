# 0055 — Syntax-highlighter code tables → `<pre>` (code formatting)

- **Date:** 2026-06-18
- **Tag:** `0055-codetable`  (baseline: 0054 / d3f6f57)
- **Status:** landed — code-formatting quality win, zero regression.

## Bug (user-flagged: code formatting matters)

GitHub blob/gist (and some highlighters, e.g. Crayon) render code as a `<table>`: one `<tr>`
per line, a line-number "gutter" `<td>` + a code `<td>`. jusText made each `<tr>` its own
paragraph, so the code came out (a) with every line in a separate block joined by a **blank
line** (`\n\n`) and (b) with its **indentation stripped** by whitespace normalization. Gold
keeps the code as one block with single `\n` and preserved indentation.

This is the half 0052 never addressed — 0052 only tried the data-table row-merge, which the
gist code didn't even qualify for. Revisiting per user priority.

## Fix

`rewrite_code_tables(dom)` (preprocessing, after `preprocessor`): a `<table>` with ≥4
line-number gutter cells (GitHub `data-line-number`/`blob-num`, Crayon `crayon-num`) is
rewritten to a single `<pre>` whose text is the code cells joined by `\n` (3+ newlines
collapsed to 2). The existing verbatim `<pre>` path then preserves indentation and line
structure. **Gate is deliberately tight** — `lineno`/`de1`/`de2`/`gutter` are EXCLUDED because
MediaWiki diff tables use them (an earlier broad gate false-matched 12 diff/data tables).
Tight gate matches exactly 1 dev doc (gist), 0 false positives.

## Results (0055 vs 0051/0054, all datasets dev)

| dataset | F1 | Lev |
|---|--:|--:|
| general | 0.8852 (flat) | 0.8206 → **0.8208** |
| code/math/science/table | flat | flat |
| **gist doc** | 0.850→0.849 (token noise) | **0.679 → 0.726 (+0.047)** |

Aggregate flat (general Lev +0.0002), **the gist code now renders with correct indentation
and single-newline lines, matching gold nearly char-for-char** — the meaningful visualized
code-quality win ([[data-quality-counts-without-metrics]]). F1 is token-based so it can't
reward indentation; judged on the rendered output, not the metric. 61 tests pass.

## Next

- `roseindia` / general line-per-`<p>` or `<div>` code joined `\n\n` vs gold `\n` — a
  different structure (no line-number gutter); needs a separate, careful detector.
