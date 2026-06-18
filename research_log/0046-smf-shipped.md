# 0046 — SMF (Simple Machines) role-transform (shipped)

- **Date:** 2026-06-18
- **Tag:** `0046-smf`
- **Status:** landed — correct role data; minor general regression (user-accepted).

## What

SMF handler after SE/vBulletin/phpBB. SMF posts are `div.post` (body in nested `.inner`)
paired with a sibling `.poster`; date in a header `.smalltext`. Author/date scoped via
`_post_container`; body = `.inner` (drops the signature/"Logged" chrome wrapping it); quotes
KEPT (SMF gold keeps them, unlike vBulletin). Fires only with >=2 usernamed posts.

## Results

- Correct usernames + dates across skins: arduino (psteve / pYro_65 / Adrculda), adventure-
  cycling (SlowAndSlower / staehpj1 / John Nelson).
- Fires on 8 dev docs; general/dev 0.8850 -> **0.8847** (-0.0003), Lev 0.8202 -> 0.8200;
  domains flat; 61 tests pass.

Shipped per the user's directive (correct role-to-front data worth a minor general F1 dip).
Residual: quote-header chrome ("Quote from: X on date" vs gold's "Quote:") + bold-vs-plain
format are the small per-doc cost; the role attribution (the point) is correct.

## Forum coverage

SE (0031) · vBulletin (0039) · phpBB (0040) · SMF (0046) shipped. Remaining: XenForo
(body-chrome), bbPress, the "other/unknown" tail (no general detector — 0043).
