# 0094 — vBulletin threaded mode (posts in the pd[] preview-data array)

- **Date:** 2026-06-25
- **Tag:** `threaded-dev3` (baseline: `0093`)
- **Status:** landed — 4 vBulletin threaded forums recovered, dev +0.0010, dev2/dev3 flat-to-up.

## Trigger

User: `wakeworld.com/forum/showthread.php?p=644317&mode=threaded` scored **0.252** — only the open
post extracted; the other ~23 posts were missing.

## Cause

In `?mode=threaded` only the opened post is real DOM. Every other post's HTML is stashed in a JS
**preview-data array** `pd[postid] = '...escaped html...'` (rendered on click), so jusText sees one
post. Playwright wouldn't help — previews load on *click*, not on render. But the bodies are in the
raw page, so a pure rule recovers them.

## Fix

`vbulletin_threaded_paragraphs`: parse the `pd[]` entries from the page scripts, de-escape the JS
string literals, and per entry emit `username: body` (author link with parens stripped; the bbcode
`Quote:` block removed). Gated on >= 3 `pd[]` entries containing a `post_message` div (vBulletin
threaded signature), placed after the linear vBulletin handler.

## Results — generalizes (the point)

dev3 is a 0.01% sample, so a pattern here recurs at scale. The handler fired on **4** vBulletin
threaded forums across dev+dev3 and improved every one:

| doc | before | after |
|---|--:|--:|
| webdeveloper.com (dev) | 0.176 | **0.945** |
| sencha.com (dev) | 0.506 | 0.757 |
| littleriveroutfitters (dev3) | 0.553 | 0.759 |
| wakeworld (dev3) | 0.252 | 0.377* |

dev 0.8917→0.8927, dev3 0.8865→0.8866, dev2 0.8804 flat. 61 tests pass. Fires 0× on dev2.

*wakeworld is capped by its gold: the thread has ~23 posts but the gold kept only ~7. We now
recover ALL posts with correct attribution -- the content is NOT missing; the metric is the gold's
subsetting (see [[gold-underextracts]]). Other threaded forums (no such subsetting) reach 0.76-0.95.

## Follow-ups (same cycle, user-flagged)

- **OP username (threaded):** the thread-starter has no member link in its `pd[]` entry, so its
  posts were unattributed. Use the post's own `postmenu_<id>` span (present for every post, incl.
  the OP) for the display name, with the member link as fallback. brian1000's posts now attributed.
- **Lost reply after a quote (threaded):** removing the bbcode quote `<div>` also dropped its TAIL
  text -- which is the actual reply (bhyatt_ohp "What about resurrecting a post from 2006?" vanished).
  `_drop_keep_tail` reattaches the tail before removing the node.
- **Linear no-`.postbit` skins:** the same wakeworld skin in `mode=linear` (and zonealarm, ...) has
  real `post_message` divs but no `.postbit`, so the main vBulletin handler missed it -> author
  after the body + login handle instead of display name. `vbulletin_postmessage_paragraphs` anchors
  on `post_message` divs, reads the author from the header anchor (`<strong>`-display name, else
  `(handle)`) + date, and emits author-to-front via the shared assembler.
  **wakeworld linear 0.929->0.995**, zonealarm flat. dev 0.8927, dev2 0.8804 (flat), dev3 ->0.8867.
