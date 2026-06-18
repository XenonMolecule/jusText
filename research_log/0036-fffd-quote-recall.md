# 0036 — FFFD repair: 1-char fallback tier (quote/dash recall)

- **Date:** 2026-06-18
- **Tag:** `0036-fffd2`
- **Status:** landed — quality win (quote recall), zero regression.

## Idea

The 0029 FFFD table (2-before, 2-after context) is high-precision but low-recall on **curly
quotes** — their contexts are too varied to clear the ≥3-sample bar, so lohud still showed
18 `�`. Added a **(1-before, 1-after) fallback tier** (≥5 samples, ≥85% from train), applied
only after the 2-char tier misses. The 1-char contexts are clean and quote/dash-dominated:
`,`+`�`+` `→`"` (×302), `.`+`�`+` `→`"` (×90), ` `+`�`+`I/S/O`→`"` (opening), ` `+`�`+` `→`–`
(×143), plus contraction apostrophes. Accents stay safe — the specific 2-char tier handles
`K`+`�`+`pp`→`ö` first.

## Results

- lohud residual `�`: **18 → 6** (curly quotes recovered).
- FFFD docs (88): F1 0.8874 → **0.8878**, Lev 0.8208 → **0.8215**.
- general/dev: **0.8849 / 0.8191 (unchanged)** — recovered chars are a tiny fraction of 1000
  docs. Domains flat (FFFD is general-only). 61 tests pass.

## Verdict

Metric-neutral on the aggregate, real readability win on the affected docs, zero regression —
the data-quality bar. 62 1-char contexts added to `_char_repair.py`. The 6 residual `�` on
lohud are rare proper-noun accents (e.g. `K�ppen`) correctly left alone (no confident guess).
