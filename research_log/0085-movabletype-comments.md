# 0085 — Movable Type comment attribution

- **Date:** 2026-06-25
- **Tag:** `mt-comments-dev2` (baseline: `0084`)
- **Status:** landed — sauer-thompson 0.887→0.915, dev2 +0.0001, dev flat (no regression).

## Trigger

User: sauer-thompson.com "missing attribution of the comments which is pretty critically
important." We kept the three comment bodies but dropped *who said each one*. Gold:
```
Comments

Annon (December 10, 2012 10:59 AM):
We are downbeat because...

Nan (December 10, 2012 11:05 AM):
...
```

## Why the existing comment path missed it

`_comment_author_meta` (0068/0070) is WordPress-shaped: it scans `div/li/article[id^=comment-]`
with the author in `.fn`/`cite`. sauer-thompson is **Movable Type**: each comment is a
`div.comment-content` body followed by a sibling `p.comment-footer` byline
"Posted by: &lt;name&gt; | &lt;date&gt;" — author/date come *after* the body, in a different
element, so the wrapper-id scan found nothing and bailed early.

## Fix

`_movabletype_comment_meta`: pair each `p.comment-footer` ("Posted by: NAME | DATE") with the
`comment-content` immediately preceding it. Wired as the fallback when the WordPress scan finds
<2 comments, then reuses the shared `prepend_comment_authors` to insert a `*author* (date):`
marker before each kept comment.

Also fixed a **duplicate-header** bug surfaced here: `prepend_comment_authors` always injected a
`**Comments**` heading, but Movable Type pages already keep their own `<h3>Comments</h3>` — so it
doubled. Now the injection is skipped when a `Comments`/`Comments (N)` header is already kept
(WordPress pages have none, so they are unaffected).

## Results

sauer-thompson 0.887 → **0.915** F1 (0.817 → 0.843 Lev) — three comments now attributed.
dev2 0.8803→0.8804, dev 0.8913→0.8913 (flat). 61 tests pass.

## Next

- ask.metafilter.com (queued): commenter-to-front, different engine — needs its own meta reader.
