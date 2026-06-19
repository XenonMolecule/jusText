# 0068 — Highlight blog-comment authors before the comment (WordPress)

- **Date:** 2026-06-18
- **Tag:** `current-wpcom` (baseline: `current-faq`)
- **Status:** landed — user-prioritised quality fix; full-dev −0.00006 F1 (within the
  data-quality rule).

## Trigger

User, on SAP (`blogs.sap.com/.../sap-hana-workaround`) and thethirdestate: "we were not
highlighting the person before the comment ... pretty important to me." The gold writes each
comment as `*author* (date):` then body; we kept the body but **dropped the author** (the
comment header is short/link-heavy, so the model drops it).

## Why a blanket transform fails, and the fix

Of 214 docs with WordPress comment structure, gold keeps comments in only **26%** — no
learnable signal (comment-count and avg-length both ~flat). A transform that *resurrects* or
*de-chromes* comments craters (−2.3 F1 sum, mostly resurrecting threads gold drops). So the
fix is **post-classification and additive only**:

`prepend_comment_authors` prefixes `*author* (date):` onto the **first KEPT paragraph** of each
comment the model already keeps -- it never resurrects a dropped thread, so volume (a spammy
80-comment blog) doesn't matter: if the model dropped the spam, we add nothing.

Two extraction bugs found while checking regressions (and fixed):
- **`Permalink` as author** (nokiabreak): author was read from the first `<a>` in the header,
  which was the permalink link. Now read `.fn`/`.comment-author-link`/`cite` text and skip
  non-name tokens (`Permalink`/`Reply`/`says`/…). Recovers the real name ("Chris").
- **Pingbacks/trackbacks** (mjtrim) counted as comments. Now skipped by class.

## Results (5 datasets dev, vs current-faq)

- SAP: F1 0.9615 → **0.9787**; renders `*Fernando Da Ros* (April 11, 2014 at 1:48 am):` first.
- general F1 **−0.000063** / Lev −0.000038; code/math/science/table flat. 61 tests pass.
- Dev: 23 affected docs, 5 win / 9 lose (small). The losses are docs where the model **leaks
  spam comments** gold drops (e.g. nokiabreak's "Great items from you, man…") — a pre-existing
  precision leak this only labels, not the formatting. Net is negligible, accepted under the
  user's data-quality rule for the visualized author-before-comment win.

## Not covered / next

- thethirdestate uses a one-off `div.ucomment` theme (no `.comment-content`, ordinal+`@` date
  format); the standard handler doesn't fire on it. Deferred as a separate narrow case.
- The deeper lever is the **model leaking spam comment bodies** on gold-drop docs (the source
  of every loss here) — a classifier problem, not a formatting one.
