# 0086 — Ask MetaFilter / MetaFilter engine handler

- **Date:** 2026-06-25
- **Tag:** `metafilter-dev2` (baseline: `0085`)
- **Status:** landed — all 5 metafilter docs +0.06–0.09 F1, dev2 +, dev flat (no regression).

## Trigger

User: ask.metafilter.com/233299 "parses really well, but I do still prefer when the commenter
comes first before the comment" + "having the number of favorites... is still quite great." The
gold already fronts the commenter — `**username** (TIME, DATE):` before each answer — so the
preference matches the gold and is a clean metric win.

## Structure

Each answer is a `div.comments` whose trailing `span.smallcopy` byline reads
`posted by <user> at <TIME> on <DATE> [N favorite(s)]`. Question title is the `h1` carrying a date
suffix (stripped); question body is `div.copy` (not `.smallcopy`); the gold separates question from
answers with a `---` rule. `metafilter_paragraphs` rebuilds: title → question body → `---` → per
answer `**user** (TIME, DATE) [N favorites]:` + body. Gated on ≥2 valid bylines, placed last in the
forum_qa chain.

## Two notes

- **Favorites kept** (user decision, recorded in QUEUE): the gold drops them, so `[N favorites]`
  diverges slightly — but the commenter-to-front structural gain dominates, so every doc still
  improves. Quality + metric both win here.
- **Bug caught wiring it in:** question-body paragraphs from `ParagraphMaker` aren't `class_type
  ="good"`, so `is_boilerplate` filtered them out (233299 cratered to 0.30 in-pipeline though the
  prototype gave 0.97). Fixed by marking handler-emitted body paragraphs "good", same as
  `_forum_thread_paragraphs` does (line 945).

## Results

| doc | base | handler |
|---|--:|--:|
| 233299 | 0.891 | **0.965** |
| 191629 | 0.888 | 0.947 |
| 59330 | 0.846 | 0.909 |
| 110216 | 0.752 | 0.834 |
| 216973 | 0.862 | 0.953 |

dev2 0.8804→0.8804, dev 0.8913→0.8913 (both flat — the 5 wins are 1 dev2 + 4 train, no false
fires). 61 tests pass. Title-date inclusion is gold-inconsistent across the 5 docs (caps the
achievable F1) but is minor.
