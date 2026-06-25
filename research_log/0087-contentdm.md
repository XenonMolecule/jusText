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
(`.encode().decode("unicode_escape")` then `json.loads`), and emit `item.item.text` — gated on the
CONTENTdm `collectionAlias` key AND text ≥ 400 chars. That gate fires on exactly the 2 item-OCR
docs and on NONE of the other 203 dev3 `__INITIAL_STATE__` SPAs or the 2 empty-text CONTENTdm items
(they fall through to normal extraction). Placed last in the forum_qa chain.

## Results

westlake 0.00→0.99, uidaho 0.00→0.19 (correct content, gold-capped). dev3 0.8821→0.8827 (+0.0006 F1, Lev +0.0005).
dev2/dev flat (CONTENTdm is dev3-only; gate can't fire elsewhere). 61 tests pass.

## Next

- augie (`collection.pageText`) and digitalhorizons (Title + caption) need extra branches — low
  ROI (2 dev3-only docs, different formats). Deferred.
