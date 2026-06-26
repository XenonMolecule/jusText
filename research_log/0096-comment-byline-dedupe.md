# 0096 — Duplicate comment byline (raw `.comment-meta` + injected marker)

- **Date:** 2026-06-25
- **Tag:** `dbl2-dev3` (baseline: `0095`)
- **Status:** landed — everybodylikessandwiches 0.583→0.586, dev2/dev/dev3 flat (no regression).

## Trigger

User: some comments show the byline twice -- the raw `Spare Ribbon September 11, 2008 at 4:19 pm`
AND the injected `*Spare Ribbon* (September 11, 2008 at 4:19 pm):`. Only for SOME comments.

## Cause

For those comments the classifier kept the raw `.comment-meta` byline as its own paragraph;
`prepend_comment_authors` then injected its marker too -> the byline appears twice.

## Fix

After matching comments, mark as boilerplate any kept paragraph that is just a raw byline -- it
contains a matched comment's author AND date and is no longer than `len(author)+len(date)+15`. The
injected marker remains the single byline.

## Results

everybodylikessandwiches 0.583 → 0.586 (no more double bylines). dev2 0.8804, dev 0.8927,
dev3 0.8867→0.8868 -- all flat. 61 tests pass.
