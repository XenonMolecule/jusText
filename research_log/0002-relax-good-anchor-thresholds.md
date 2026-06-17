# 0002 — Relax the "good"-anchor thresholds

- **Date:** 2026-06-16
- **Tag:** `v3.0.2-<sha>` (baseline compared against: `v3.0.2-9fb3340`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed

## Hypothesis

jusText is **recall-limited: it drops too much**. On `general/dev`, 60 docs return
*nothing* (EMPTY_PRED, F1=0) and 103 under-extract — together ~+0.11 of headroom.

Mechanism (confirmed via the analysis API): a paragraph is labelled `good` only if
`stopword_density ≥ 0.32` **and** `length > 200` chars. `neargood` paragraphs are
promoted only when adjacent to a `good` anchor. 57/60 empties are clean **English**
text (recoverable), with per-doc *max* stopword density 0.583 — well above 0.32 — but
**no paragraph exceeds 200 chars**, so they cap at `neargood`, get **zero anchors**,
and the whole doc collapses to boilerplate. The 200-char `length_high` is the binding
constraint, not stopword density. (Whitespace was ruled out: perfect whitespace
normalization moves Lev-sim only +0.005.)

Relaxing the thresholds that gate `good`/`neargood` should recover dropped content and
lift both F1 and Levenshtein similarity.

## What changed

Retuned the library default classification thresholds in `justext/core.py` (originally
tuned for CleanEval, not this LLM-distilled gold):

| param | old | new |
|---|--:|--:|
| `LENGTH_LOW_DEFAULT`     | 70   | 40   |
| `LENGTH_HIGH_DEFAULT`    | 200  | 60   |
| `STOPWORDS_LOW_DEFAULT`  | 0.30 | 0.15 |
| `STOPWORDS_HIGH_DEFAULT` | 0.32 | 0.20 |

Chosen by grid sweep on `general/dev` (F1-maximizing; precision held ~0.81, so not just
trading precision for recall). `max_link_density` left at 0.2 (no gain).

## Results

`general`, F1 / Lev-sim, vs. baseline `v3.0.2-9fb3340`:

| split | F1 before→after | Lev before→after | empties |
|---|---|---|--:|
| dev   | 0.762 → **0.809** (+0.047) | 0.682 → **0.725** (+0.043) | 60 → 17 |
| train | 0.768 → **0.809** (+0.042) | 0.687 → **0.724** (+0.037) | — |

dev and train move identically → not overfit to dev. `compare` on dev: 475 improved,
398 regressed, 127 unchanged. Net **+0.047 F1**.

Domain sets (F1 Δ, both splits; the new defaults are library-wide):

| dataset | train | dev |
|---|--:|--:|
| code    | +0.119 | +0.155 |
| math    | +0.239 | −0.074 |
| science | +0.015 | −0.010 |
| table   | +0.004 | +0.044 |

Big wins on `code`/`math` (technical text — same root cause). The `math`/`science`
*dev* dips are on 2–3-doc splits (noise — their train splits rose). `table` is still
~0 — boilerplate-classified tables need dedicated handling, not threshold tuning.

## Insights

- **Confirmed the diagnosis.** The huge improvements are exactly the recovered
  empties (0 → ~0.95): weather.gov, ferc.gov, racket-lang list, stackexchange — all
  clean text that previously had no `good` anchor.
- **A real precision tradeoff appeared.** The 398 regressions are moderate (top losses
  −0.2 to −0.38, e.g. instructables, blogspot) — lower thresholds now admit some
  boilerplate. Net still strongly positive, but **boilerplate leakage is the new
  dominant failure mode** → the lever for 0003.
- Parameter tuning alone tops out ~0.81 F1 on dev. The 0.90 target needs algorithmic
  changes (anchor logic, precision filtering).

## Next

- Parameter tuning plateaus ~0.81 F1 on dev; reaching 0.90 needs algorithmic work.
- Candidate 0003: let high-stopword `neargood` clusters self-anchor (no `good`
  neighbour required) — directly targets the remaining no-anchor collapses.
- Then the PARTIAL middle (426 docs @ 0.82) and OVER_EXTRACT (boilerplate leakage).
- Domain sets (esp. `table`) untouched — separate cycles.
