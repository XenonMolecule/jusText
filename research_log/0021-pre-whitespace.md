# 0021 — Preserve <pre>/<textarea> whitespace (code indentation)

- **Date:** 2026-06-17
- **Status:** landed — quality fix (user-requested), no benchmark regression.

## Problem (found via the user's report inspection)

jusText's `Paragraph.text`/`append_text` run `normalize_whitespace`, collapsing the
indentation inside `<pre>` code (e.g. `\n    <meta…` → `\n<meta…`). Code came out
unindented — wrong/unusable for code docs (user examples: interactiveonline HTML5-iPhone,
roseindia). Newlines survived (normalize keeps a LF) but leading indentation didn't.

## Fix (`core.py` + `paragraph.py`)

Track `<pre>`/`<textarea>` depth in `ParagraphMaker`; inside it, append characters
**verbatim** (no normalize, don't skip blank) and mark the paragraph `verbatim`.
`Paragraph.text` returns verbatim paragraphs with whitespace intact (only trims outer
blank lines). `words_count`/`stopwords_density` still use `.split()`, so classification
features are unaffected.

## Result

Indentation now preserved (`\n\n    <meta name="viewport"…`). Benchmark impact (fast
model): general 0.858→0.858 (flat — few docs have `<pre>`), **code 0.834→0.836**,
math/science/table unchanged. All 61 unit tests pass. Net: genuine output-quality fix,
slight code gain, zero regression.
