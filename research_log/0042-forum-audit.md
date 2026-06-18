# 0042 — Forum coverage audit (the case for a general detector)

- **Date:** 2026-06-18
- **Status:** audit — reframes forum work toward a general detector.

## Finding

The gold applies the username-to-front reorder to **111/1000 dev docs** (11%!) — counting the
`Name (Date):` / `**Name** (date)` / `**Question/Answer**` formats. Per-engine handlers
(SE/vBulletin/phpBB) cover only **29**:

| engine | dev docs | handled |
|---|--:|--:|
| other/unknown | 58 | 0 |
| StackExchange | 20 | 20 |
| vBulletin | 20 | 4 |
| phpBB | 8 | 5 |
| XenForo | 3 | 0 |
| SMF | 2 | 0 |

Per-engine detection is whack-a-mole: skin variation means even vBulletin is 4/20, and
**58 docs (52%) have no recognized engine signature**. User-supplied examples confirm the
spread: arduino/adventurecycling (SMF), spacefellowship (phpBB variant), wehavelupus (vB skin
we miss). SMF where it DID fire was +0.0233 F1 — the transform is right, detection is the wall.

## Conclusion: build the general detector (0041)

The universal forum signal is **repeated post blocks each anchored by a username link**
(`href` ~ `/(members?|users?|u|profile)/` or class `author`/`username`). With the robust
`_post_container` scoping (0039) now available, the plan:
1. Gate hard: >=3 distinct user-anchored blocks with substantial text (avoids the 0032
   non-forum false fires).
2. Per block: username = the user link; body = the block's content. **Open problem**: cleanly
   separating body from username/date/signature without a per-engine body selector — likely
   reuse jusText's own good/bad classification on the block, or take the block's longest
   paragraphs.
3. Format `**username** (date)`; strip quote blocks.

This would catch the 58 other/unknown + the missed skins — the real "huge win where
available" — and would also fix the `<ol>` misfire (forums bypass the list logic). Validate on
the 111-doc forum subset AND non-forum docs (no regression).

## Shipped per-engine (kept)

SE (0031, +0.109 on SE), vBulletin (0039, neutral/correct), phpBB (0040, +0.0155). These stay;
the general detector runs as a fallback after them.
