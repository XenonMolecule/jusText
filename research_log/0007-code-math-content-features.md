# 0007 — Code/math-aware content features (domain-agnostic)

- **Date:** 2026-06-17
- **Tag:** `0007-content-features` (vs `0004-dom-features`)
- **Commit:** `eaa7880`
- **Status:** landed — NEGATIVE (features reverted; plateau confirmed again)

## Hypothesis

Code/math content has **low natural-language stopword density** (so jusText's heuristic
classifies it boilerplate) but **high symbol/digit density and indentation** — signals
the classifier currently lacks. Adding cheap, **domain-agnostic** content features
(digit ratio, symbol/operator ratio, line-indentation ratio) should help `code` and
`math`, and — since `general` has technical/`has_code` docs (which lag: 0.827 vs 0.865
non-table) — likely lift `general` too. (User's bet: math/code fixes help general.)

Quick negative noted first: stripping raw-HTML artifacts (`<!-- -->`, `<br>`) from
output is −0.0003 F1 — ROUGE tokenizes them away. Cosmetic, not a lever.

## What changed

`justext/classifier.py`: appended 3 cheap features — `digit_ratio`, `symbol_ratio`
(operators/brackets `{}()[];=<>|/\*+&%$#@^`), `indent_ratio` (fraction of lines
starting with whitespace). Retrained the general model.

## Results — NEGATIVE (reverted)

Adding digit/symbol/indent features (retrained RF):

| dataset/split | before (0004) | after | Δ |
|---|--:|--:|--:|
| general/dev | 0.8469 | 0.8471 | +0.000 |
| general/train | 0.8496 | 0.8504 | +0.001 |
| code/dev | 0.814 | 0.817 | +0.003 |
| math/dev | 0.811 | 0.809 | noise (2 docs) |

Flat. The new features didn't even enter the top importances — the model still leans
on `not_boilerplate`/`cf_good`/`cf_bad`/`link_density`. **Reverted** (they added
per-char cost for no gain; runtime is a hard objective).

Also tested a **sequential-smoothing** post-process (flip isolated keep/drop based on
neighbours): **also negative** (0.847 → 0.840) — isolated decisions are usually correct
and the context features already encode neighbours.

## Insights

- The plateau is robust: labels, DOM, threshold, model-type, content features, and
  smoothing all fail to move general past ~0.847. The model is a smoothed heuristic and
  the extra signals don't add discriminative power for the diffuse hard cases.
- Cosmetic fixes (dashes, whitespace, HTML artifacts) don't move the metric — ROUGE/Lev
  are robust to them. Headroom is whole-paragraph decisions only.

## Next

- **0008: code & math structural deep-dive** (per user). Stop reusing the general model;
  look at *why* code/math paragraphs fail — likely jusText **segmentation** of
  `<pre>`/`<code>`/equation blocks, which a feature can't fix but a parsing rule can.
