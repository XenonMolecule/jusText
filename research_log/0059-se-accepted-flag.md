# 0059 — StackExchange accepted-answer flag (quality signal, user opt-in)

- **Date:** 2026-06-18
- **Tag:** `current-seaccept` (baseline: `current-xenforo`)
- **Status:** landed — deliberate quality signal at ~zero full-dataset metric cost.

## Trigger

User: an accepted answer "should probably be retained" —
`stackoverflow.com/questions/7244080/...openfire`. Investigation showed the accepted answer
is **already retained**: `stackexchange_paragraphs` keeps every `//div[starts-with(@id,
"answer-")]`, and 0/all SE-domain dev docs fall through to the model. So there is no
retention bug; the only available delta is the `(accepted)` **label** the gold sometimes adds.

## Gold is inconsistent (measured)

Among 101 SE docs (train+dev) with an accepted answer in the DOM, the gold writes
"(accepted)" in only **44**. Split by answer count:

| thread | gold marks accepted | gold omits |
|---|--:|--:|
| single answer | 3 | 16 |
| multi (2+) | 41 | 41 |

Single-answer threads almost always omit it (nothing to contrast); multi-answer is a
coin-flip with **no learnable pattern** — same wall as SE comment-inclusion (0034) and the
XenForo marker formats (0058).

## Decision

Unconditional flag: dev −0.004 F1 / −0.019 Lev (5 win, 7 lose). Gated to multi-answer
threads: dev −0.0006 F1 / −0.0065 Lev (still trades ~1:1, Lev cost where gold omits it). I
recommended **not** shipping (chasing inconsistent gold). User invoked the data-quality rule
and opted to ship the **multi-answer-gated** flag as a semantic signal they value — naming
the canonical solution — accepting the negligible metric cost.

## Change

In `stackexchange_paragraphs`, on threads with >1 answer, append " (accepted)" to the marker
of the answer whose `<div>` carries class `accepted-answer`. Single-answer threads unchanged.

openfire (the cited doc): `**Answer (Flow)** (accepted)`; F1 0.9384 → 0.9399, Lev 0.8817 →
0.8866.

## Ship gate (5 datasets dev, vs current-xenforo)

- general F1 −0.000001, Lev −0.000007 (flat)
- code −0.0001 F1, math −0.0005 F1 (one SE doc each in those tiny splits where gold omits
  the flag); science/table flat
- 61 tests pass.

"Approximately no regression on the full dataset" ([[data-quality-counts-without-metrics]]),
with the accepted answer now explicitly flagged. Not a gold-match win — a chosen quality
signal.
