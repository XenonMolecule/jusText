# 0070 — Comment author on its own line, before the first line (fixes 0068)

- **Date:** 2026-06-18
- **Tag:** `current-cmarker` (baseline: `current-urlfix`)
- **Status:** landed — placement fix, metric-neutral, matches the gold's format.

## Trigger

User on SAP: "someone's name for the comment appears AFTER the first line." 0068 inline-prefixed
`*author* (date):` onto the first paragraph **≥15 chars**, so a short greeting (`Hi Krishna,`,
11 chars) was skipped and the marker landed on the *second* line. The gold puts the author on
its **own line** above the comment:

```
*Fernando Da Ros* (April 11, 2014 at 1:48 am):
Hi Krishna,

I think it's an option yes ...
```

## Fix

`prepend_comment_authors` now **inserts a separate `_marker_paragraph`** before each comment's
first KEPT line (matched by `body.startswith(text)` to catch short greetings, falling back to
an in-body match when the greeting itself was dropped). Still additive + post-classification:
only comments the model already keeps get a marker; dropped threads are never resurfaced.

## Results (5 datasets dev, vs current-urlfix = 0068 inline)

- SAP: F1 0.9787 → **0.9797**; renders the author on its own line, then `Hi Krishna,`, then
  the body -- matching the gold.
- general F1 −0.000003 / Lev −0.000012 (neutral); code/math/science/table flat. 61 tests pass.

The inline→separate-line change is metric-neutral in aggregate but corrects the placement on
every kept-comment doc (visualized quality, [[data-quality-counts-without-metrics]]).

## Follow-up: `**Comments**` heading

The gold opens the kept comment section with a `**Comments**` heading (100% of the 56
comment-keep docs). We now emit it before the first comment marker. SAP 0.9797 → **0.9802**;
general dev neutral. (The `---` rule the gold sometimes adds is only 41% consistent -- skipped.)

## Not fixed (Problem 2)

The user also flagged dropped short context lines (a comment's `Interesting solution.` intro,
the author's `Krishna Tangudu` sign-off). Those are the **model dropping short paragraphs** --
force-keeping the rest of a kept comment was measured net-negative (resurrects spam on the
74% of comment docs where gold drops the thread). That's the comment keep/drop wall (0068),
a classifier problem, not a formatting one. Deferred.
