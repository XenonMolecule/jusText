# 0011 — Text-content stack on the new segmentation (best F1, runtime cost)

- **Date:** 2026-06-17
- **Tag:** (experiment on `0009-row-merge` segmentation)
- **Commit:** `b4f4be5`
- **Status:** landed — measured, **NOT shipped** (runtime). Best F1 to date.

## Idea

Combine the two positive levers: 0009 segmentation (cleaner row/list/post paragraphs)
+ the 0008 text-content stack (char 3–5gram HashingVectorizer + SGD-logistic on the
paragraph text, stacked as a probability feature into the RF). The cleaner paragraphs
should let the text model discriminate better than on the old fragmented segmentation.

## Results (general/dev)

| model | F1 | Lev | predict ms/doc |
|---|--:|--:|--:|
| struct RF (0009, shipped) | 0.849 | 0.772 | ~3 |
| text-only | 0.809 | 0.712 | ~8 |
| **struct + text stack** | **0.854** | **0.778** | ~11 |

+0.005 F1 / +0.006 Lev over 0009 — and bigger than the same stack on the old
segmentation (0008: +0.0035). Text-only also rose (0.795→0.809): cleaner paragraphs help.

## Decision

**Not shipped.** +8 ms/doc roughly triples the original inference budget (~5.5→~17 ms/doc
total), and runtime is an explicit hard objective. +0.005 F1 doesn't justify 3× latency.
Recorded as the **highest-F1 config available** if the runtime budget is ever relaxed.

## Insight

Even combining every positive lever, general tops out ~**0.854 F1 / 0.778 Lev** — still
short of 0.90/0.85. The oracle is 0.902/0.838, and the 0.6-overlap oracle itself
*under-counts* code/diverse-token content (those paragraphs score 0.3–0.6 overlap even
when they're real content), so the true reachable ceiling is a bit higher but needs a
smarter label, not a knob. The honest conclusion stands: fast CPU-only paragraph
selection caps below the target; >0.90 needs a heavier (semantic/generative) paradigm.

## Next

- User decision: (a) accept ~0.85 (strong, fast result); (b) relax runtime → ship the
  text-stack for +0.005; (c) invest in a heavier paradigm for >0.90.
