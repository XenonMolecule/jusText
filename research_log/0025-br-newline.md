# 0025 — `<br>` → newline (line structure)

- **Date:** 2026-06-17
- **Tag:** `0025-br`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — quality win (line structure), F1-neutral, Lev net-positive.

## Idea

User: "we are severely lacking newlines where they can actually be useful"
(law.drake.edu faculty page). Diagnosis: the publications list there is **`<br>`-separated**
(not `<li>`), and jusText collapsed each single `<br>` to a **space**, blobbing the list
into one line. The gold respects `<br>` line breaks. Many pages use `<br>` for structure
(addresses, contact blocks, `<br>`-separated lists/publications).

Fix: a single `<br>` now emits a **newline** instead of a space (core.py
`startElementNS`). `normalize_whitespace` keeps it because the whitespace run contains a
`\n`. `<br><br>` still becomes a paragraph break (unchanged). One-line change.

## Results (general/dev, ftstack model, 1000 docs)

| | space (before) | newline (after) |
|---|--:|--:|
| F1 | 0.8803 | 0.8803 |
| Lev | 0.8160 | 0.8161 |

Per-doc: **F1 unchanged on all 1000** (token metric is whitespace-agnostic). Lev:
**129 improved, 59 regressed, 812 flat**; total gain +0.159 vs loss −0.052 = **net +0.107**
(3:1), worst single regression −0.011. Domains (code/math/science/table dev) flat — no
regression. The 59 minor regressions are decorative `<br>` in flowing prose.

## Verdict

Metric-flat on the mean but **net-positive** and a real structural/quality win (the user's
"newlines where useful"). The original +0.0034 from a 300-doc subset did not generalize —
the subset was unrepresentative; full-set truth is flat-mean / net-positive per-doc. Shipped.

## Note for a later cycle

- Code indentation is already preserved (0021 `<pre>` verbatim); residual is ragged mixed
  tabs/spaces (expandtabs is metric-neutral). A linter is NOT advisable (forum code is
  partial/broken/mixed). 
- Deferred (user): dropped spaces on some contentdm pages (olemiss/cgsc) — separate cycle.
