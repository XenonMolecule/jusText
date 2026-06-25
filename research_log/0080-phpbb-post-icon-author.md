# 0080 — phpBB "Post"-as-author bug (post-icon link)

- **Date:** 2026-06-25  **Tag:** phpbbauth-dev2  **Status:** landed — 15 wins, 0 losses.

## Trigger
User: dhammawheel posts all titled "**Post**" instead of the commenter. Newer phpBB skins put
a post-icon link `<a><span class="imageset icon_post_target" title="Post">Post</span></a>`
BEFORE the author link in `.author`, so `links[0]` = "Post" for every post.

## Fix
In `phpbb_paragraphs`, skip author links that wrap an `imageset`/`icon` span or whose text is a
generic label (Post/Reply/Quote/…); take the first real link, or the "by <name> »" text as a
fallback. dhammawheel now: `**mogg**`, `**kirk5a**` (correct).

## Results (rawhtml)
phpBB sweep (dev2+dev+train): SUM dF1 +0.2265, **15 wins, 0 losses**. dev2 +0.00004 / dev
+0.00001 (small aggregate — markers are few tokens — but pure correctness, zero regression).
61 tests pass. Standard phpBB3 (author link first, no icon) is unaffected.
