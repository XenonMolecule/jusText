# 0040 — phpBB role-transform (shipped, positive)

- **Date:** 2026-06-18
- **Tag:** `0040-phpbb`
- **Status:** landed — correct role data, small net-positive.

## What

phpBB handler, after SE (0031) and vBulletin (0039). phpBB's `.postbody` holds both the
author line ("by <name> on <date>") and the post `.content`, so each postbody is the post
scope. Author = first `.author` link; date parsed from the author text after "on"/"»"; body
= `ParagraphMaker` on the quote-stripped `.content`. Reuses the shared `_forum_thread_paragraphs`
assembler + `_strip_quote_blocks`. Fires only when >=2 posts have author + content.

## Results

- Correct markers: sublimetext → `**Saxi** (Fri Nov 08, 2013 5:39 pm)`, `**tito** (...)`,
  matching the gold's authors + dates.
- Fires on **10 dev docs**; fired-doc F1 **0.8762 → 0.8917 (+0.0155)** -- phpBB extracts
  cleanly (author+content co-located), so it's a genuine win, not just neutral.
- general/dev **0.8848 → 0.8850** (Lev 0.8197 → 0.8200); domains flat; 61 tests pass.

## Forum coverage so far

SE (0031, +0.109 on SE) · vBulletin (0039, neutral, correct) · phpBB (0040, +0.0155 on
fired). Shared assembler + quote-strip + `_post_container` make adding engines cheap.
Next: XenForo (`.message-body`/`.bbWrapper`), then a fastText router for the long tail.
