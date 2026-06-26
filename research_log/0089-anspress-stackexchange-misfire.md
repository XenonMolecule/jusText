# 0089 — StackExchange handler misfires on AnsPress (buries the answer)

- **Date:** 2026-06-25
- **Tag:** `anspress-dev3` (baseline: `0088`)
- **Status:** landed — housingforseniors 0.07→0.98, dev2/dev/dev3 flat-to-up (no regression).

## Trigger

User (repeatedly, "this devastates me"): `housingforseniors.com/Questions/How-is-Alzheimers-…`
scored **F1 0.07** — we emitted only `**Question**` / `**Answer**` role markers and **dropped the
entire answer body**, even though the answer text is fully present in the HTML.

## Root cause

`stackexchange_paragraphs` fired on this page, which is **not** StackExchange — it's the **AnsPress**
WordPress Q&A plugin. AnsPress reuses StackExchange-looking hooks: `<div id="question">`,
`<div id="answer-N">`, and schema.org `itemprop="text"` on the question. So the handler passed its
gate, emitted the role markers, read the short *question* via `itemprop="text"` — but the **answer**
body lives in `.ap-answer-content` (no `.post-text`, no `itemprop`), so it captured nothing. The
handler returned a hollow shell that replaced the (correct) normal extraction.

## Fix

Require a real StackExchange `.post-text` body element, not just `<div id="question">`:

    if not questions or not dom.xpath('//*[contains(@class,"post-text")]'):
        return None

AnsPress has **zero** `.post-text` elements, so it now falls through to normal extraction
(F1 0.977). Real StackExchange always has `.post-text`, so SE pages are unaffected. (Also added a
`body_added` safety net: if no post body is ever emitted, return None.)

## Results

housingforseniors 0.07 → **0.977**. Only 1 AnsPress-style doc exists (dev3; 0 in dev2/dev), but the
gate change touches every SE page — verified surgical: of all docs the old gate fired, **32 real
StackExchange docs still fire** (all have `.post-text`) and **exactly 1 lost it** (housingforseniors,
the intended fix). dev3 0.8841→0.8846, dev2 0.8804 flat, dev 0.8913 flat. 61 tests pass.
