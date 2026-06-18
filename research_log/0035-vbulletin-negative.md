# 0035 — vBulletin forum handler (NEGATIVE, not shipped)

- **Date:** 2026-06-18
- **Status:** negative — regresses; not shipped.

## Attempt

Built a defensive vBulletin handler mirroring the SE one (0031): detect `#post_message_N`
bodies (≥2) each with an `a.username`; emit `**username** (date)` + body via ParagraphMaker;
fall back to the normal path otherwise.

## Why it failed

- **Fires too broadly**: 38/1000 dev docs match the structure, but only ~20 are the gold
  role-transform targets. The other ~18 are vBulletin pages the gold did NOT transform
  (single posts, non-thread page types, or articles) — transforming them **regressed 15
  docs >0.02 F1**.
- **Low ceiling even on targets**: forum threads are already F1 0.890 (vs SE 0.790 — far
  less room), and the gold's date format is inconsistent (`February 5th, 2011,` →
  `February 5 2011` on one page, comma kept on another). Net target gain only **+0.003 F1**.

Detection can't distinguish "gold applied the transform here" from "didn't" — the same
unpredictability found for comment-inclusion (0034) and the SE-doc-level noise. SE worked
because it's one clean engine with a big per-doc gap; vBulletin is low-room + ambiguous.

## Verdict

Not worth the regression. Forum-thread generalization beyond SE needs a reliable
"should-transform" signal we don't have. **Deferred** — revisit only if a clean detector
emerges (e.g. the fastText router trained on big_train could gate it). The SE handler (0031)
remains the high-value forum win.
