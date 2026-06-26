# 0101 — Valid-markdown tables + tooltip leak + dash normalization

Follow-up to 0100, after review found the ragged output did not actually *render*. The 0100 harness
asserted the data was present (substring checks) but never checked the markdown was valid -- a real
gap. This adds an actual GFM render check (python-markdown) to the harness and a corpus scan.

## Three fixes

**1. UniProt `<p>` leak (everywhere, not just tables).** 0100/da05a86 scoped the display:none strip to
`table[.//th]`, so the tooltips on UniProt's *section headings* still leaked escaped `<p>` help markup
(14 lines). Fixed in `preprocessor` by stripping the hidden *content* of tooltip widgets globally,
gated on BOTH a `tooltip` class (case-insensitive) AND `display:none` -- so it hits only the hidden
payload span, never the visible wrapper whose inner text is the real label ("Active site"), and never
the layout-table content a broad display:none strip removed (−0.0056 dev2). Tail-preserving.

**2. Ragged tables rendered as INVALID markdown.** Two causes, both found with a real GFM validator:
* *Trailing empty cells.* A row padded `name | v1 | v2 | v3 | ` has a trailing empty cell that GFM
  silently drops, making it one column short of its 5-col siblings -> the whole table fails to parse
  (genomebiology: header 9 cols vs body 10). Fix: `_pipe_row` now `&nbsp;`s the *last* empty cell too.
* *Bare section lines.* atsdr's `ORGANICS`/`INORGANICS` colspan rows have no pipes, which ends the
  markdown table -> everything after collapses into one paragraph. Fix: `_render_ragged_table` splits
  the table at 1-cell rows into per-section sub-tables (blank-line separated, bold `**heading**`),
  carrying a header-only leading group onto its data section -- matching the gold's two-table layout.

**3. Dash-run cells.** The source's "no data" placeholders (`<p align=center>- --------</p>`) rendered
as ugly variable-length dash runs. `_cell_text` collapses an all-dash/underscore cell to a single
en-dash `–` (what the gold uses).

## Verification (the part 0100 skipped)
Harness `check_flagged.py` now renders output with python-markdown and asserts: no pipe-text leaks as
a `<p>`, and the target docs produce ≥N `<table>`s. Corpus scan of every doc containing a `--- | ---`
separator: **dev2 26 table-docs / 0 unrendered, dev3 46 / 0 unrendered.** atsdr -> 3 valid tables,
genomebiology -> 2, both with all data; UniProt `<p>` gone, "Active site"/"Function" kept.

dev2 0.8804→**0.8806** (+0.0002), dev3 0.8867 flat. 61 tests pass; 16-check harness ALL PASS.
