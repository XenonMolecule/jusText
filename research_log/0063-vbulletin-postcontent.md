# 0063 — vBulletin 4: stop stripping the `blockquote.postcontent` body wrapper

- **Date:** 2026-06-18
- **Tag:** `current-vb4` (baseline: `current-dblnum`)
- **Status:** landed — largest win of the session. general +0.0008/+0.0010, code +0.0047/+0.0062.

## Trigger

User: "Were we still not able to fix this one? and why?" —
`dbforums.com/showthread.php?991464-...` (vBulletin). The handler didn't fire and the doc
fell to the model (F1 0.9379).

## Why it failed

`vbulletin_paragraphs` finds the post bodies (`post_message_`) and the usernames (Joozh,
rafala) correctly. But each body is run through `_strip_quote_blocks`, which removed **every**
`<blockquote>` — and **vBulletin 4 wraps the entire post body in
`<blockquote class="postcontent restore">`**. So the strip deleted the whole post (raw 10
paragraphs → 0), every post was dropped, `<2 posts` → handler returned None. The `.//blockquote`
strip exists for phpBB (which quotes in `<blockquote>`); it was never meant to hit the vB4
content wrapper.

This is the "vB4 wall" the queue noted — but it was a **bug**, not a gold-inconsistency: the
content wrapper was being mistaken for a reply-quote.

## Fix

One xpath change in `_strip_quote_blocks`: exclude the wrapper.

```python
.//*[contains(@class,"quote")] | .//blockquote[not(contains(@class,"postcontent"))]
```

Real reply-quotes (bbcode `.quote`/`.bbcode_quote`, phpBB `<blockquote>`) are still stripped;
the vB4 body survives, so the handler fires across the whole vB4 install base.

## Results (5 datasets dev, vs current-dblnum)

| dataset | F1 | Lev |
|---|--:|--:|
| general | 0.8855 → **0.8862** (+0.00077) | 0.8219 → **0.8229** (+0.00098) |
| code | 0.8496 → **0.8542** (+0.00467) | 0.7534 → **0.7596** (+0.00617) |
| math / science / table | flat | flat |

Per-doc sweep across all forum docs (train+dev): **227 changed, ΣΔF1 +3.67, ΣΔLev +7.84**.
On dev: general **18 improved (+0.88) vs 3 regressed (−0.11)**; code 1 improved, 0 regressed.
dbforums itself F1 0.9379 → 0.9653, Lev 0.9205 → 0.9476. 61 tests pass.

## Regressions (minor, known shape)

The 3 dev regressions (raptorsrepublic −0.08, badmintoncentral −0.02, sencha −0.005) and the
train cluster (zonealarm, mathhelpforum, conservativeunderground) are the gold-keeps-quotes
minority — docs whose gold retains reply-quotes the handler strips. Net is +3.67 F1 across
227 docs, so they're dwarfed; not worth a quote-keep gate (which craters the majority, cf.
0058 XenForo).

## Insight

A shared helper (`_strip_quote_blocks`) silently gating a whole engine: the vB4 content
wrapper happened to be a `<blockquote>`, so the phpBB-oriented strip nuked it. Engine bodies
should never be removed by the quote-stripper — only nested quotes.
