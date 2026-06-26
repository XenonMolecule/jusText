# 0098 — MediaWiki/Wikia math images dropped (class="tex") + richer LaTeX→text

- **Date:** 2026-06-26
- **Tag:** `latex-tex` (baseline: `v4.2.0`)
- **Status:** landed — math recovered (was fully dropped); dev2/dev3 flat (0 such docs), math domain ~flat (gold-capped).

## Trigger

User (alarmed): a math doc where we **drop the math entirely** -- e.g. `var(X) = E[(X – μ)²]`. The
expression is NOT in the HTML as text; it's a **MediaWiki/Wikia math image**:
`<img class="tex" alt="\operatorname{var}(X) = \operatorname{E}((X-\mu)^2)" src=".../math/...">`.
jusText drops `<img>`, so the formula vanished. (70 such images in that one variance article.)

## Why 0065 missed it

`recover_latex_images` (0065) gated on the renderer **host** (codecogs/mimetex/...). MediaWiki/Wikia
serve math from their own image host with the formula in `alt` and a `class="tex"` marker -- no host
match, so nothing fired.

## Fix

- **Gate:** also fire on `img.class` containing `tex` (older MediaWiki/Wikia) or
  `mwe-math-fallback-image-inline` (current MediaWiki). Covers Wikipedia/Wikia/every MediaWiki -- a
  large population at scale (dev3 is a 0.01% sample).
- **`_latex_to_text`:** transcribe Greek letters (`\mu`→μ, `\sigma`→σ, ...) and common symbols
  (∞, ×, ≤, ∑, →, ...) instead of dropping them; superscripts (`^2`→²); `\operatorname{var}`→`var`
  / `\mathrm{E}`→`E`; tighten paren spacing. `\mu` now → μ (was → "").

## Results

`\operatorname{var}(X) = \operatorname{E}((X-\mu)^2)` → `var(X) = E((X - μ)²)` (gold:
`var(X) = E[(X – μ)²]`). The math is **recovered** (was dropped). Metric impact is small/gold-capped:
dev2/dev3 have **0** `class="tex"` docs (no regression possible there); the one math/test doc that
fires is separately flagged over-extraction so its F1 is capped (recovering 70 formulas vs the gold's
truncated subset). This is a **quality/recall win that generalizes** to all MediaWiki math, not a
metric mover on the current splits. dev2 0.8804 flat, dev3 0.8868→0.8867 (−0.0001, noise from one codecogs doc). 61 tests pass.
