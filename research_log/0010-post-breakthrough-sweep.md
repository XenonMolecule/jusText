# 0010 — Post-breakthrough internals sweep (what's NOT the lever)

- **Date:** 2026-06-17
- **Tag:** (analysis on `0009-row-merge`)
- **Commit:** `1b1196b`
- **Status:** landed — all negative; documents the search boundary.

After the 0009 segmentation win (oracle 0.893→0.902), swept the obvious follow-ups to
free the rest of the headroom. None helped general:

| lever tried | result |
|---|---|
| Re-tune length/stopword thresholds for new (longer) segmentation | current ll40/lh60 still best (0.809 heur); raising length_high hurts |
| Keep `<form>` content (preprocessor `forms=False`) | general oracle flat; table oracle +0.004. Not a lever |
| Language: non-English docs | only 11 likely-non-English in general/dev (+14 borderline); max upside **+0.005**. Not worth multilingual complexity for an English-dominated set |
| Block separator (`\n` vs `\n\n` join) | gold uses both (19k/16k); single-`\n` slightly worse Lev. `\n\n` stays |

## Insight

`general` now sits at **model 0.849 / oracle 0.902** (ceiling gap 0.053). The gap is
**MODEL_LIMITED** (101 docs, model 0.604 vs oracle 0.918, +0.032) and **diffuse** — no
structural or preprocessing knob moves it. The model collapses to ~0 on a few
non-English/technical docs (heuristic-feature reliance) but those are too few to matter
for general.

The real wins this phase came from **structure** (0009 segmentation: table +0.24,
oracle raised), not tuning. The residual general gap is the fast-classifier
discrimination limit vs the teacher's semantic judgment.

## Next

- Lev target (0.85) needs oracle Lev > 0.85; currently 0.838 (raised by 0009). Further
  formatting structure (not cosmetic) is the only path — investigate intra-block layout.
- Otherwise: the honest standing is general 0.849/0.772 (from 0.762/0.682), table
  0.45 (from 0.0). Strong, fast, CPU-only. 0.90/0.85 likely needs a heavier paradigm.
