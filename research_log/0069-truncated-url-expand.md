# 0069 — Expand truncated autolink URLs (phpBB/vBulletin)

- **Date:** 2026-06-18
- **Tag:** `current-urlfix` (baseline: `current-wpcom`)
- **Status:** landed — net-positive win. general +0.00008 F1 / +0.00012 Lev, 4 datasets flat.

## Trigger

User: a forum post's Amazon URL is botched —
`pianosociety.com/.../viewtopic.php?p=52248`:

```
ours: http://www.amazon.com/Fundamentals-Pian ... 755&sr=8-1
gold: http://www.amazon.com/Fundamentals-Piano-Practice-Chuan-Chang/dp/1419678590/ref=sr_1_1?ie=UTF8&qid=1327213755&sr=8-1
```

phpBB/vBulletin shorten a long URL in the **displayed anchor text** (`prefix ... suffix`)
while keeping the full URL in `href`. jusText emitted the truncated visible text; the gold
keeps the full URL.

## Fix

`expand_truncated_urls(dom)` (run first, before the forum handlers read the DOM): for a plain
autolink `<a href>` whose visible text matches `^(https?://\S+?)\s*\.\.\.\s*(\S+)$`, replace
the text with `href` **iff** the href starts with the shown prefix and ends with the shown
suffix. The prefix/suffix guard means a tracking/redirect href that doesn't correspond to the
displayed URL is left untouched, and anchors with child elements are skipped.

## Results

- 199 docs (train+dev) have the truncation pattern: **ΣΔF1 +0.67, ΣΔLev +1.11**. Small loss
  cluster (worst −0.025) where the gold itself truncates/omits the URL; dwarfed by the wins.
- 5 datasets dev (vs current-wpcom): general F1 0.8862 → **0.8863** (+0.000077), Lev 0.8229 →
  **0.8230** (+0.000118); code/math/science/table flat. 61 tests pass.
- pianosociety: F1 +0.0142, Lev +0.023 — full Amazon URL restored.

## Insight

A rare case where the *displayed* text is deliberately lossy and the attribute holds the
truth — the inverse of most extraction, where text is canonical. The prefix+suffix match
keeps it safe without a per-engine gate (fires across phpBB/vBulletin/IPB autolinks alike).
