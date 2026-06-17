# 0022 — Mojibake repair (input encoding fix)

- **Date:** 2026-06-17
- **Tag:** `0022-ftfy`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — data-quality win, zero metric regression.

## Idea

User flagged broken characters in output (e.g. laughspin/Tom-Papa). Diagnosed as
**mojibake**: the source `html` field arrives already mis-decoded (UTF-8 bytes read as
Latin-1/CP1252, sometimes *twice* → `Ã¢â‚¬â„¢` for `’`). It is **in the input string**,
not a jusText decode bug — the 8B teacher repaired it (gold is clean), jusText faithfully
emitted the garbage.

Fix: repair the input with `ftfy.fix_encoding` before parsing, but **only when a mojibake
signature is present** (`MOJIBAKE_PATTERN`), so clean docs are byte-for-byte untouched.
ftfy is an **optional** dependency (lazy import; no-ops if missing). New
`justext(..., fix_encoding=True)` param (default on) + `repair_mojibake()` helper.

## Results

| | F1 | Lev |
|---|--:|--:|
| general/dev flagged docs (8) | 0.7649 → **0.7664** | 0.6815 → **0.6821** |
| general/dev full-mean effect | +0.00001 | +0.00000 |

- Prevalence: **43/10000** general/train, **8/1000** general/dev, **0** in all domain
  sets (code/math/science/table). General-only, ~0.5%.
- All 8 flagged dev docs improve or hold — **no doc regresses**. Mojibake signature
  removed from every affected output.

## Verdict

Negligible on the aggregate metric (too few docs, score dominated by content selection),
but a real **output-quality** improvement on the affected docs and **zero regression**.
Shipped per the "data quality counts even without metric movement, as long as nothing
regresses" guidance. Signature-gating is what makes it safe.

## Next

Remaining user quality items: markdown headers/lists emission (measured max +0.006 Lev —
quality-only, precision-sensitive), cgsc spacing, roseindia code-line `\n\n`-vs-`\n` join.
