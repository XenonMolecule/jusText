# 0079 — Forum broadening attempts (NEGATIVE, not shipped)

- **Date:** 2026-06-25  **Set:** datasets_rawhtml dev2/dev/train
- **Status:** negative — reverted; confirms the "tight handlers only" rule.

Autonomous cycles on the dev2 forum under-extraction trend (0078). Both reverted:

## Iter 4 — phpBB keep-quotes
Some forum golds keep `>`-quoted text (dhammawheel), most drop it. Keeping quotes:
**+0.247 sum but 13 wins / 39 losses** across 106 phpBB docs — net-positive in sum yet
regresses 39 docs. Violates "don't sacrifice dev/train/test". Gold-inconsistency wall (same as
the vB4-broadening revert). Not shipped.

## Iter 5 — generalize phpBB (author from post container + span.postbody + .name)
To fire on phpBB2/variant skins (silentpcreview, linuxformat, …) that currently fall to the
model and over-extract. Broadening the author match catastrophically mis-fired:
**dev2 −2.24, dev −1.35, train −12.5** (28 wins / 111 losses). Tight, engine-specific
selectors are required; broadening regresses far more than it fixes. Not shipped.

## Takeaway
The dev2 forum frontier is a wall: quote-keeping is gold-inconsistent, and broadening handler
firing regresses heavily. The clean forum win this session was a *new tight engine* (JForum,
0077), not broadening existing ones.

## Iter 8 — lower the global classifier threshold (NEGATIVE)
The user prefers recall (less under-extraction) over precision. Lowering the keep threshold
(dev2 300-doc sample): thr=0.42 F1 −0.006 (15 up / 44 down); thr=0.35 F1 −0.016 (20 up /
84 down). The blunt global tradeoff regresses 3× more docs than it recovers (the over-extraction
the user cautioned against). Classifier is already near-optimal; not shipped.

## Iter 10 — heuristic-override for long link-free blocks (NEGATIVE)
monroecounty.gov / informatics.jax.org drop long, link-free, low-stopword content (address
lists, gene terms) that the *heuristic* keeps but the *ML model* drops. Tested override: keep a
paragraph when heuristic=good AND ML=bad AND len>200 AND link<0.1. Result (full sets): dev2
−0.0045 (+14/−115), dev −0.0031 (+12/−92). Same failure mode as the threshold lever — it re-adds
long link-free boilerplate (disclaimers, related-content, footers) on ~8× more docs than it
recovers. The ML model's low-stopword dropping is correct on balance; classifier is calibrated.
Not shipped. Recall-boosting levers (threshold, heuristic-override) are both net-negative; only
structural/handler one-offs (0076/0081 multi-doc, forum engines) ship cleanly.
