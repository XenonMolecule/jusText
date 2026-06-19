# 0064 — ParagraphMaker skips `<style>`/`<script>` text (mathhelpforum math)

- **Date:** 2026-06-18
- **Tag:** `current-styleskip` (baseline: `current-vb4`)
- **Status:** landed — quality fix, dev flat (zero regression), fixes a train cluster.

## Trigger

User, on the 0063 vBulletin win: "What do you mean there was a regression on mathhelpforum?"
Investigating `mathhelpforum.com/algebra/67637`: every equation came out as
`img.top {vertical-align:15%;}`. mathhelpforum renders math as `<img class="top">` preceded
by an inline `<style>img.top {vertical-align:15%;}</style>`. The **forum handlers run
`ParagraphMaker` on the raw post body**, bypassing the preprocessor (which strips
`<style>`/`<script>` via lxml `Cleaner`), so the CSS text leaked in where each formula
should be.

## Fix

`ParagraphMaker` now tracks a `self.skip` depth for `<style>`/`<script>` (like `self.pre`
for verbatim) and drops their text in `characters()`. CSS/JS is never document content, so
this is correct on every path — it just wasn't enforced on the forum-handler path that skips
the preprocessor.

## Results

- `mathhelpforum/67637`: F1 0.4575 → **0.5469**, Lev 0.3824 → **0.4590**; the
  `img.top {…}` junk is gone.
- 5 datasets dev: **exactly flat** (the affected mathhelpforum docs are in train; no dev doc
  has inline `<style>` in a forum body). Zero regression.
- 61 tests pass.

## Limits

This removes the CSS junk but not the underlying math: the formulas are `<img>` the gold has
as rendered LaTeX text, so the post now reads "If , evaluate" (empty where the equation
images were). Recovering the formula needs img-alt/LaTeX-src decoding — a separate, harder
problem, deferred. The regression on mathhelpforum from 0063 is materially reduced, and the
overall 0063 change remains strongly net-positive (+3.67 F1 across 227 forum docs).

## Insight

Forum handlers operate on the **raw** DOM (pre-preprocessor) to read structure the cleaner
would destroy — but that also means cleaner-provided guarantees (no script/style text) don't
hold there. Enforcing "style/script is never text" in ParagraphMaker itself closes the gap
for every current and future raw-DOM path.
