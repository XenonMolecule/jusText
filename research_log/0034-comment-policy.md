# 0034 — Comment policy: metric/corpus divergence (a flag)

- **Date:** 2026-06-17
- **Tag:** `0034-comments`
- **Status:** landed — `include_comments` flag, default off (zero metric change).

## Question (user)

How should we handle Q&A/forum **comments**? User: "dropping comments blanket is a big
mistake even if it leads to improvements" — they're real content for a training corpus.

## What the data says

On 23 SE dev pages:
- The gold **includes comments inconsistently**: 11/21 docs include ≥50% of their comments,
  8/21 include ~0%. Roughly 50/50 with only a weak (comment-count) signal — no clean
  classifier (cf. the 0024 markdown-trigger that also found no signal).
- The gold's comment **format is itself inconsistent** (`**Comments**` + `*User (date)*` on
  one page; `- **User:** text` on another).
- The DOM holds **far more** comments than any page shows (hidden/collapsed), so blanket-
  including them craters the metric: SE F1 0.899 → **0.754** (−0.145), Lev 0.823 → 0.623.

## No signal to classify on (per-comment investigation)

User pushed back on a flag ("passing the puck") and on scattered selection ("don't keep
comment #5 if it built on dropped 3-4 — keep/remove chunks together"). So I tested whether
any per-comment feature predicts gold inclusion (to keep the *right* comments):

- 159 SE comments, 74 included / 85 excluded (47%). **Included comments are NOT higher-
  scored** (0.36 vs 0.21), **NOT longer** (155 vs 182 — shorter!). `score>=1` rule:
  precision 0.42, recall 0.11.
- **Displayed-vs-hidden** also fails: displayed comments are 49% included = same as overall.

Conclusion: gold comment-inclusion is **annotator noise** — no per-comment or per-doc signal.
Matching the gold is impossible.

## Decision — uniform policy, default ON

Since we can't predict the gold, and comments are real content, and chunks must stay
together: **include the full contiguous comment thread per post, by default** (deduped, in
document order — never a scattered subset). `include_comments=False` opts out for strict
gold-matching benchmarking only.

| dataset/split | F1 (no comments → comments) | Lev |
|---|--:|--:|
| general/dev | 0.8857 → **0.8849** (−0.0008) | 0.8205 → 0.8191 |
| code/dev | 0.8418 → **0.8518** (+0.010) | +0.012 |
| math/dev | 0.8202 → **0.8597** (+0.040) | +0.069 |
| science/table | flat | flat |

Net **positive** across domains (code/math gold *includes* comments) at a negligible general
cost. Threading-intact, uniform, automatic — the unified solution, not a flag-punt. 61 tests
pass.

## Next

- Carry the same full-thread comment policy into the upcoming vBulletin/phpBB handlers.
