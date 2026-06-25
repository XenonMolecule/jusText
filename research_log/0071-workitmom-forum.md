# 0071 — Drupal-style group/forum role-transform (workitmom)

- **Date:** 2026-06-25
- **Tag:** `current-workitmom` (baseline: `current-cmarker`)
- **Status:** landed — forum role-transform, surgical (1 doc), zero regression.

## Trigger

User: `workitmom.com/groups/discussion/3274` "got messed up." Content is 100% present in the
HTML, but no forum engine matched (it's a custom Drupal group), so the per-post author/date
markers were missing and the first post's body dropped — F1 0.817 / Lev 0.688.

## Structure

Posts are `li[id^="post_"]` inside `ul#post_list`; the body is `div.body` and the byline is a
`.comment-by` line "Posted by happymom on 14th October 2008". Gold: `**happymom**
(14th October 2008)` then the post body.

## Fix

`workitmom_paragraphs`: collect `li[id^="post_"]` with a `.comment-by`, parse author+date from
"Posted by (NAME) on (DATE)", take the body from `div.body`, and feed the shared assembler
(`_forum_thread_paragraphs`). Gated on >=2 such posts; dispatched after XenForo.

## Results (5 datasets dev, vs current-cmarker)

- workitmom: F1 0.817 → **0.942**, Lev 0.688 → **0.893**.
- general F1 +0.000125 / Lev +0.000194; **exactly 1 doc changes**; other datasets flat.
- 61 tests pass.

## Next

- One-doc custom-forum template (like the FAQ/ucomment one-offs); the `.comment-by`
  "Posted by X on Y" byline is a generic Drupal pattern, so the gate is the `post_list`
  structure, not the byline. No other doc in the set matches.
