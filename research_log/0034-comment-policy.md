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

## Decision

Comments are a **benchmark-vs-corpus divergence**, not a simple include/exclude:
- **Benchmark** (match the imperfect gold): exclude → best metric.
- **Training corpus** (the real downstream goal): comments are real content; dropping them
  loses corrections/clarifications/the-answer-in-a-comment.

So: `justext(..., include_comments=False)` by default (gold-matching, **SE F1 unchanged at
0.899**, general/dev still 0.8857), and `include_comments=True` keeps per-post comments
(`**Comments**` + `- **author:** text`) for corpus generation. No silent loss; the caller
chooses per use case. 61 tests pass.

## Next

- A doc-adaptive include policy (e.g. only scored/visible comments) could narrow the gap,
  but the gold's inconsistency caps it. Revisit if a cleaner comment signal appears.
- Carry the same `include_comments` option into the upcoming vBulletin/phpBB handlers.
