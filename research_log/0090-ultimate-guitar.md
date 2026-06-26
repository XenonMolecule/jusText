# 0090 — Ultimate Guitar review body (from UGAPP store blob)

- **Date:** 2026-06-25
- **Tag:** `rescue-dev3` (baseline: `0089`)
- **Status:** landed — ultimate-guitar review 0.00→0.873, dev2/dev flat (gated, dev3-only).

## Trigger

User: `ultimate-guitar.com/reviews/compact_discs/counterparts/youre_not_you` scored **F1 0.00**.
The review renders client-side; the body is HTML stored in
``window.UGAPP.store.page.data.content`` (≈46 KB escaped HTML), not the DOM.

## Fix

`ultimateguitar_paragraphs`: parse the `UGAPP.store.page` JSON, take ``data.content``, and run it
through jusText's own **`ParagraphMaker`** (block-aware). Gated on ``data.content`` ≥ 200 chars —
only *review* pages carry it; the other UG page types (tabs/lessons/forum) have none and fall
through to normal extraction.

Two refinements after the user spotted bugs:
- **Script leak (user-flagged):** ``data.content`` embeds page-machinery `<script>` (UG's
  ``UGAPP.store.rateDescriptions``/``page.report`` widget JS). A naive `text_content()` leaked it.
  `ParagraphMaker` drops `<script>`/`<style>` (never content code — `<pre>`/`<code>` are kept), so
  the JS is gone. Also hardened the shared `_cdm_strip_html` the same way.
- **Paragraph breaks (user-flagged):** flattening to single spaces made one wall vs the gold's
  paragraphs. `ParagraphMaker` keeps `<p>`/`<br>` block structure, so the review reads in
  paragraphs.

## Results

ultimate-guitar review 0.00 → **0.905** (Lev 0.834; the residual is review metadata/ratings the
gold formats differently). Only 1 UG review doc in our data; the handler is dev3-only and can't
fire elsewhere (the `UGAPP.store.page.data.content` signature is UG-specific). dev2/dev flat.
61 tests pass.
