# 0041 (PLANNED) — General forum detector + `<ol>` misfire

- **Status:** planned (user, 2026-06-18). "General forum solution would be a huge win where
  available."

## Two linked problems

1. **`<ol>` misfire (0037)**: when a forum page ISN'T caught by a per-engine handler, it falls
   to the normal path, and vBulletin/forum structural lists get numbered — `<ol class="posts">`
   (the post list!) becomes "1. 2. 3.", `<ol class="d1">` (nav) too. Example:
   forum.wehavelupus.com/showthread.php?9181 (a vBulletin skin our handler misses).
2. **Per-engine coverage gaps**: SE/vBulletin/phpBB handled, but skins/engines without the
   exact selectors (some vBulletin, XenForo, the "other/unknown" 126-train tail) fall through.

## The general-forum idea (fixes both)

A generic fallback after the per-engine handlers: detect a thread by the **universal forum
signal** — repeated post blocks each anchored by a **username link** (`href` matching
`/(members?|users?|u|profile)/` or class `author`/`username`) — and reuse `_post_container`
(robust scoping, 0039) + `_strip_quote_blocks` + `_forum_thread_paragraphs`. If a page has
>=3 such user-attributed blocks with substantial text, treat it as a thread; emit
`**username** (date)` per post. Catching wehavelupus this way ALSO bypasses the list logic →
fixes the `<ol>` misfire for free.

Risk (from 0032): a naive general extractor fired on non-forum pages and regressed. Mitigate
with a STRONG gate (>=3 repeated user-attributed blocks) + the now-robust scoping. Measure on
the forum-thread subset AND non-forum docs; ship only if non-regressing.

## Selectivity rule for `<ol>` (if general forum doesn't land)

Make 0037 list markers skip STRUCTURAL lists: `<ol>/<ul>` whose class matches
nav/menu/post/tab/breadcrumb/pagination/sidebar/widget, or whose `<li>` items contain
block-level elements (a real list item is short/inline; a forum post is a block).

## Engines still uncovered

XenForo (`.message-body`/`.bbWrapper`, `.message-name`) — cheap to add with the shared
assembler. Then the fastText router for routing pages to the right handler / the general one.
