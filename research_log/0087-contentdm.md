# 0087 — CONTENTdm digital-library OCR text (from __INITIAL_STATE__)

- **Date:** 2026-06-25
- **Tag:** `cdm-dev3` (baseline: `0086` / dev3 0.8821)
- **Status:** landed — westlake 0.00→0.99, uidaho 0.00→0.19, dev2/dev flat (no regression).

## Trigger

dev3 survey: four `…/digital/collection/…` docs at F1 **0.00**. They're **CONTENTdm** (digital
archive software). The page renders the item client-side; the digitized full text lives in
`window.__INITIAL_STATE__ = JSON.parse('…').item.item.text`, NOT the DOM — so jusText sees only the
SPA shell and extracts nothing.

## Why it's only a partial platform win

The four docs are heterogeneous — the gold's source field differs per page type:

| doc | gold from | handler |
|---|---|---|
| history.westlakelibrary | `item.text` (OCR ≈ gold) | **0.00→0.99** |
| digital.lib.uidaho | `item.text` (49k OCR, gold is a 5k PREFIX) | 0.00→0.19 |
| np3.augie | `collection.pageText` (landing HTML) | n/a (text empty) |
| digitalhorizons | item Title + tiny caption | n/a (text < 400) |

uidaho's low score is **gold truncation**, not a bug: the gold capped its output at ~5k of a 49k
newspaper OCR and dropped pages 2–4 — all legitimate content ("Tommy Burns Speaks", ads, etc.).
Per user ("over-extracting is fine") emitting the full OCR is the *correct* extraction; the metric
is gold-limited (see [[gold-underextracts]]).

## Fix

`contentdm_paragraphs`: parse the `__INITIAL_STATE__` JS-escaped JSON
(`.encode().decode("unicode_escape")` then `json.loads`), gated on the CONTENTdm `collectionAlias`
key (so the other 203 dev3 `__INITIAL_STATE__` SPAs are untouched — verified 0 fires on dev2/dev
too). Three branches by page type:

1. **OCR item** (`item.text` ≥ 400): emit the text. westlake, uidaho.
2. **Photo / metadata item** (short `item.text`): title + caption + `collection.pageText`
   (HTML-stripped). digitalhorizons.
3. **Collection landing** (empty `item.text`): `collection.messages.SITE_CONFIG_aboutPageHtml`
   (HTML-stripped). augie.

**PUA cleanup:** CONTENTdm OCR uses a Private-Use-Area glyph (U+F0C3) as a paragraph-break marker;
the gold renders it as a blank line. `_cdm_clean_text` converts the PUA range → `\n\n` and drops
control chars — fixing both the "weird characters" and the "broken newlines" the user flagged on
westlake (one root cause).

## Results

| doc | base | handler |
|---|--:|--:|
| westlakelibrary (OCR) | 0.00 | **0.995** |
| digitalhorizons (photo) | 0.00 | **0.979** |
| augie (collection) | 0.00 | **0.968** |
| uidaho (OCR, gold-truncated) | 0.00 | 0.191 |

dev3 0.8821 → **0.8837** (+0.0016 F1, Lev +0.0015). dev2/dev flat. 61 tests pass.
