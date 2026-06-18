# 0026 — Keep whitespace between inline elements (fix mashed words)

- **Date:** 2026-06-17
- **Tag:** `0026-space`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — **F1 win + quality fix.**

## Idea

User: "Why do spaces get dropped on something like this?" (contentdm pages — olemiss
lomax, cgsc). Our output mashed words: `datatransmissioncapabilities`, `staffis`,
`taskoverload`, `VeraHall'sgrandfather`.

Root cause: these CMS pages render each word/field as its own inline element
(`<a>data</a> <a>transmission</a>`). The whitespace **between** the elements arrives as a
blank text node, and `ParagraphMaker.characters()` did `if is_blank(content): return` —
dropping it, so adjacent words fused.

Fix: when a blank text node has preceding text in the paragraph, append a **single space**
instead of dropping it. `normalize_whitespace` collapses any run, so it can never
double-space; `self.br` is left untouched so `<br> <br>` still makes a paragraph break.

## Results (ftstack model)

| dataset/split | F1 | Lev |
|---|--:|--:|
| **general/dev (1000)** | 0.8803 → **0.8825 (+0.0022)** | 0.8161 → **0.8165** |
| code/dev (11) | 0.8391 → **0.8423 (+0.0032)** | 0.7398 → **0.7415** |
| science/dev (3) | 0.9886 (flat) | 0.9748 |
| math/dev (2) | 0.828 → 0.821 | — |
| table/dev (2) | 0.399 → 0.388 | — |

General **+0.0022 F1** is the largest single-cycle gain since 0019 — mashed words were
token-match failures (`datatransmission` ≠ `data`+`transmission`), so un-mashing recovers
recall *and* precision. math/table dips are 2-doc-split noise (verified: LaTeX `$3x^2+3$`
intact, no math notation wrongly spaced). 61/61 unit tests pass.

## Verdict

Real quality bug (the user spotted it) **and** a metric win. Current best general/dev now
**0.8825 / 0.8165**. Shipped.
