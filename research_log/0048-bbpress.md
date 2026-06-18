# 0048 — bbPress (WordPress) role-transform (shipped)

- **Date:** 2026-06-18
- **Tag:** `0048-bbpress`
- **Status:** landed — clean positive (5th forum engine).

## What

bbPress handler after SE/vBulletin/phpBB/SMF. Clean per-post selectors: body
`.bbp-reply-content`/`.bbp-topic-content`, author `.bbp-author-name` (nearest ancestor).
Reuses the shared assembler + quote-strip. Fires with >=2 authored posts.

## Results

- Correct authors: kriesi.at (SoftFocus/Devin), buddypress.org (Tammie/Paul Gibbs/@modemlooper),
  studiopress (peripatew — a user's-replies page, all one author, correct).
- dev: fires 1, ΔF1 +0.0061; **train: fires 7, ΔF1 +0.0229** (validated train-as-dev).
- general/dev 0.8847 -> **0.8848**, Lev 0.8200 flat; domains flat; 61 tests pass.

Forum engines now: SE (0031) · vBulletin (0039) · phpBB (0040) · SMF (0046) · bbPress (0048).
Clean because bbPress has a dedicated body element (unlike SMF's chrome / vB4's blockquote body).
