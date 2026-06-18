# 0049 — Skip list markers on structural lists (fix 0037 misfire)

- **Date:** 2026-06-18
- **Tag:** `0049-list-skip`
- **Status:** landed — fixes the 0037 `<ol>` misfire; general +0.0002/+0.0005.

## Bug

0037 numbered/bulleted EVERY `<ol>/<ul>` `<li>`. On forum pages a per-engine handler misses
(e.g. wehavelupus, a vB skin), the post list `<ol class="posts">` and nav `<ol class="d1">`
fell to the normal path and got numbered "1. 2. 3." (user-flagged). The block-aware fix tried
earlier broke gist (real list items wrap text in `<p>`); item SIZE isn't knowable in SAX.

## Fix

Skip markers when the list's `class` flags it non-content: a substring match against
nav/menu/tab/crumb/sidebar/widget/toolbar/social/share/related/**posts**/comment/footer/
header/breadcrumb/links. Content lists (gist's `<ol class=None>`) keep their markers.

## Results

- wehavelupus numbered-post misfire: **gone** (0 spurious "N." lines). gist numbered list:
  **kept**.
- general/dev 0.8848 -> **0.8850** (Lev 0.8200 -> **0.8205**), **science 0.9874 -> 0.9883**,
  code +0.0002, math flat. 61 tests pass.

The spurious markers were widespread (not just wehavelupus), so removing them is a small net
metric win as well as a quality fix.
