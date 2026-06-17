# 0001 — Baseline (jusText v3.0.2, unmodified)

- **Date:** 2026-06-16
- **Tag:** `v3.0.2-9fb3340`
- **Commit:** `b2ee3fa`
- **Status:** landed (reference point)

Stock jusText against the LLM-distilled gold (`final_output`), no changes. This is
the number every future entry diffs against. Metrics: ROUGE-L F1 (LCS, word tokens)
and char-level Levenshtein similarity (newlines/spaces count).

## Results

Each cell is **ROUGE-L F1 / Levenshtein similarity** (both mean, higher is better):

| dataset | train | dev | test | docs (tr/dv/te) |
|---|--:|--:|--:|--:|
| general | 0.768 / 0.687 | 0.762 / 0.682 | 0.773 / 0.690 | 10000/1000/1000 |
| code    | 0.581 / 0.446 | 0.616 / 0.509 | 0.458 / 0.308 | 44/11/4 |
| math    | 0.440 / 0.306 | 0.793 / 0.659 | 0.356 / 0.282 | 8/2/2 |
| science | 0.711 / 0.582 | 0.949 / 0.904 | 0.414 / 0.358 | 14/3/2 |
| table   | 0.013 / 0.037 | 0.000 / 0.000 | 0.561 / 0.503 | 6/2/5 |

Lev-sim runs ~0.06–0.10 below F1 everywhere (it penalizes the whitespace/newline
differences ROUGE ignores), but tracks it closely. **Domain splits are tiny (2–5
docs) and intentionally so — per-split means are noisy; trust direction, not
decimals.** `general` is the reliable signal (F1 within 0.011 across all splits).

## Insights (current failure modes, from `general/dev` + domain runs)

- **Whole-table collapse is the worst failure.** `table` ≈ 0 on train/dev: jusText
  discards tabular content as boilerplate. Biggest single gap.
- **Technical/symbolic text is penalized.** `has_code` docs score 0.595 vs 0.784
  without; `code`/`math` sit ~0.15–0.3 below `general`. Stopword-density + min-length
  heuristics punish code/equations (low stopword ratio, short lines).
- **Empty predictions:** 6% of `general/dev` return *nothing* (`EMPTY_PRED`), almost
  all technical or non-English pages — guaranteed zeros.
- **Length errors:** ~10% under-extract (ratio <0.5), ~8% over-extract (>1.5).
- **Whitespace:** jusText collapses internal whitespace (gold `49%   x` → `49% x`).
  Real but small (2 docs in dev) — a cheap Levenshtein win, negligible for ROUGE.
- **Language:** English stoplist hardcoded; non-Latin pages score ~0. Few in
  `general` but a structural limitation.
- **Hard crashes:** jusText raised on 12 `general/train` + 1 `test` docs (caught by
  the harness, scored as empty). Worth root-causing.

## Next (hypotheses to test, roughly by expected payoff)

1. **Tables** — stop dropping `<table>` content; flatten cells to text. Target `table`.
2. **Code/short blocks** — relax stopword-density / min-length so code survives.
   Target `code`, `math`, the `EMPTY_PRED` tail.
3. **Language-aware stoplist** — detect language or union stoplists. Target `NON_LATIN`.
4. **Preserve whitespace** — cheap Lev-sim gain; verify it doesn't hurt ROUGE.
5. **Fix the ERROR docs** — investigate the ~13 crashes.

Tooling note: gold↔pred↔metrics join is **position-based** (domain sets have null/
duplicate ids by design). Test split is guarded in both `run_eval.py` and the viz
loader — re-enabled only for deliberate milestone runs.
