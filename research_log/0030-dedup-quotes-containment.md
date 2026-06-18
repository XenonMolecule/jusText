# 0030 — Dedup: quote-normalize + containment

- **Date:** 2026-06-17
- **Tag:** `0030-dedup2`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — general +0.0005 F1 / +0.0006 Lev, fixes visible duplication.

## Idea

User flagged lohud.com as "a big failure": its intro appeared **twice** in our output. The
two copies are the same text but (a) one has **curly apostrophes + a U+FFFD**, the other
**straight apostrophes**, and (b) one is a **shorter teaser** of the other. The 0018 dedup
(exact `fuzz.ratio >= 97` on raw text) missed both: the encoding diff drops ratio below 97,
and the length diff (teaser vs full) defeats the equal-length ratio.

Fix to `_dedup_kept`:
- **Normalise** curly/straight quotes (`’‘‛→'`, `“”„→"`) and strip `�` before comparing,
  so the same text in different encodings matches.
- **Containment**: also drop a paragraph (≥40 chars) that is a near-exact substring of an
  earlier, longer kept one (`partial_ratio >= 98`) — repeated teasers/excerpts.

## Results (ftstack model)

| dataset/split | F1 | Lev |
|---|--:|--:|
| **general/dev (1000)** | 0.8827 → **0.8832** | 0.8169 → **0.8175** |
| code/dev (11) | 0.8423 → 0.8421 | flat (noise) |
| math/science/table | flat | flat |

lohud intro now appears **once** (was 2×). Aggregate up across many docs (dedup is general,
not lohud-specific). 61/61 tests pass.

## Note / residual on lohud

lohud still scores ~0.74 — remaining issues are NOT the dup: 18 leftover `�` are **curly
quotes** the 0029 table doesn't cover (varied contexts; high-precision table = low recall on
quotes), plus a paragraph-ordering difference vs the gold and "A A" / "Written by"
boilerplate. Those are separate, smaller, and partly content-selection-bound.
