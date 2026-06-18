# 0039 — vBulletin role-transform (shipped, correctness-first scoping)

- **Date:** 2026-06-18
- **Tag:** `0039-vb`
- **Status:** landed — correct role data, metric-neutral. (Fixes the 0038 misattribution.)

## Fix

0038 mis-attributed posts (wrong username) because the container walk overshot to a shared
ancestor on some skins. Replaced it with `_post_container`: the **largest ancestor of a post
body that contains no other post body** — i.e. the post's own block. Author/date are read
from that block; `<blockquote>`/`.quote` blocks are stripped so a post quoting an earlier one
isn't duplicated.

## Correctness (the whole point)

Per-post usernames are now right across skins:
- thefiringline: `[helike1, SDC, gyvel]` (0038 wrongly gave helike1 to all)
- codeguru: `[lasha, Skizmo, jnmacd, ovidiucucu]`
- traxxas: `[dustyfingerz, Jersey Jato, RC-Fan, ...]`

## Results

Fires on **16 dev docs** (skins with `#post_message_N` + extractable usernames; others fall
back safely). 

| dataset/split | F1 | Lev |
|---|--:|--:|
| general/dev (1000) | 0.8848 (flat) | 0.8195 → **0.8197** |
| fired docs (16) | 0.9020 → 0.9014 (−0.0006) | — |
| code/math/science/table | flat | flat |

Metric-neutral, correct role-to-front data — the data-over-metric ship the user chose, now
without the corpus-poisoning bug. 61 tests pass. `**username** (date)` format matches the
gold's spirit (its exact format varies per page; not chased).

## Coverage / next

Covers vBulletin skins exposing `#post_message_N`. Skins without it (e.g. some mp3car) fall
back. phpBB / XenForo would need their own body selector but can reuse `_post_container` +
quote-strip. The fastText router could later gate broader coverage.
