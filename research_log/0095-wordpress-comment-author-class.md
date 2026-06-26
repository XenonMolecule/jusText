# 0095 — WordPress comment author in `.comment-author` (broaden selector)

- **Date:** 2026-06-25
- **Tag:** `cauth-dev3` (baseline: `0094`)
- **Status:** landed — everybodylikessandwiches 0.55→0.58, dev2/dev/dev3 flat (no regression).

## Trigger

User: comments section "missing" on `everybodylikessandwiches.com/.../soup-for-2...` (F1 0.55). We
kept the comment *bodies* but dropped the `**Comments**` header and every `*author* (date):` marker.

## Cause

`_comment_author_meta` found the 26 `id="comment-*"` containers but read the author only from
`.fn` / `.comment-author-link` / `cite`. This (Blogger-on-WordPress) theme puts the author in a
plain **`.comment-author`** span, so author resolved to "" and the whole comment was skipped (no
marker). The date ("September 10, 2008 at 11:57 am") was already matchable.

## Fix

Broaden the author selector from `comment-author-link` to **`comment-author`** (a superstring that
still matches `comment-author-link`). The date/body logic is unchanged.

## Results

everybodylikessandwiches 0.547 → **0.583**: `**Comments**` + all 26 `*author* (date):` markers now
emitted. (The residual gap is some short comment bodies the classifier drops -- the recall frontier,
separate issue.) dev2 0.8804, dev 0.8927, dev3 0.8867 (all flat -- the single-doc win rounds away). 61 tests pass.
