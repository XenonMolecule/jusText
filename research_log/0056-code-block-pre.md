# 0056 — Multi-line `<code>` blocks → `<pre>` (code indentation)

- **Date:** 2026-06-18
- **Tag:** `0056-codeblock`  (baseline: 0055 / 9566b8b)
- **Status:** landed — code-formatting quality win, zero real regression.

## Bug (code formatting, user priority)

Many sites wrap a whole code listing in `<code>` (often in a styled box), using `<br>` for
line breaks and `&nbsp;` for indentation (e.g. roseindia tutorials). jusText kept the line
breaks (`<br>` → newline, 0025) but **lost the indentation**, because `<code>` isn't verbatim
so whitespace normalization collapsed the leading `&nbsp;`. 23 dev docs have multi-line
`<code>` blocks.

## Fix

`rewrite_code_blocks(dom)` (preprocess): a `<code>` element that is a real code listing —
**>80 chars AND contains `<br>`** — is converted to a verbatim `<pre>`. `_code_block_text`
serializes it with `<br>` → `\n` (stripping any source newline already in the br tail, so a
pretty-printed `line<br>\nline` doesn't double-space) and `&nbsp;` (U+00A0) → space, then
collapses 3+ newlines.

Two gates earned by measurement:
- **require `<br>`** (not just a source newline): excludes a JSON-data blob in `<code>`
  (chroniclingamerica) that the gold renders differently — it regressed −0.006 without the
  gate. Real br-delimited code blocks (cboard 3–58 brs, roseindia 29) keep firing.
- **lstrip the br tail's leading newlines**: fixed a double-newline regression (cboard error
  output, gold uses single `\n`).

## Results (0056 vs pre-code-fix baseline d3f6f57, all datasets dev)

- general F1 flat, Lev 0.8207 → **0.8208**; code/math/science/table flat. No real regression.
- Per-doc gains: gist +0.0471 (0055), cboard contests **+0.0025**, cboard cplusplus −0.0005
  (rounding); roseindia (train) F1 0.964→0.971, Lev 0.873→**0.900** — indentation restored.
- 61 tests pass.

Aggregate flat, **code now renders with its indentation and clean line breaks** — the
visualized data-quality win ([[data-quality-counts-without-metrics]]); F1 can't reward
indentation so it's judged on the rendered code, not the metric.

## Next

- general line-per-`<p>`/`<div>` code (no `<code>`/gutter signal) — harder, needs a
  code-likeness detector; deferred.
