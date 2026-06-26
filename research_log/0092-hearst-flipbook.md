# 0092 — Hearst flipbook slideshow (per-photo tips in a JS array)

- **Date:** 2026-06-25
- **Tag:** `flipbook-dev3` (baseline: `0091`)
- **Status:** landed — countryliving 0.21→0.95, dev2/dev flat (gated on the JS slide array).

## Trigger

User: `countryliving.com/homes/halloween-party-decor` scored **F1 0.21** — we got the article intro
but dropped the body. The body is a **slideshow**: each decorating tip is a slide whose `title` +
`description` live in a JS array, not the DOM:

    var FBModel = { type: "flipbook_2", slides: [
      { id:"slide1", slidetype:"image", title:"Halloween Entry Hall",
        description:"Dress up an entry hall with an inexpensive Halloween garland…" }, … ] }

This is the **Hearst** flipbook gallery, used across their network (Country Living, Good
Housekeeping, ELLE, …).

## Fix

`_hearst_flipbook_slides` regex-extracts each slide's `title`/`description`, unescapes the JS string
(`json.loads('"…"')`) and strips its HTML (reusing `_cdm_strip_html`), and emits `Title – description`
lines. Applied as a post-classification **append** (not a replace) so the normal extraction's article
intro is kept and only the missing slides are added. Self-limited: fires only when the page has a
`slidetype:` array AND ≥ 2 slides are absent from the output.

## Results

countryliving 0.21 → **0.947** (Lev 0.899) — intro + all 13 slide tips. Only 1 flipbook doc in dev3,
but the gate (`slidetype:` JS array) is Hearst-specific and can't fire elsewhere. dev2/dev flat.
61 tests pass.

## Other docs from the same user batch (NOT fixed — no clean/generalizable solution)

- **wakeworld** (0.93): vBulletin *threaded* mode (no `.postbit`); body extracts fine, only the
  `author (date):` markers are missing. Narrow display-mode variant, low value.
- **publiclab** (0.09) & **bmcinfectdis** (0.07): content-selection walls — the main content (a wiki
  summary; an article abstract) is in the DOM but the classifier keeps site chrome / the review
  timeline instead. A per-platform handler (Public Lab Rails; Springer) wouldn't generalize and
  would risk regressions — exactly what the user asked to avoid.
