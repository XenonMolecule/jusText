# 0093 — Research/medical abstract rescue (JSON-LD, gated on under-extraction)

- **Date:** 2026-06-25
- **Tag:** `abstract-dev3` (baseline: `0092`)
- **Status:** landed — bmcinfectdis 0.07→0.94, refinery29 0.28→0.51, dev2/dev flat.

## Trigger

User worry: "we are losing medical content" on `bmcinfectdis.biomedcentral.com/.../peer-review`
(F1 0.07). The page surfaces only the peer-review *timeline*; the article **abstract** (the gold) is
in the DOM but out-competed by chrome. The abstract is also in JSON-LD `description` (2453 chars),
which scores **0.988 vs gold** on its own.

## Why a blanket JSON-LD append fails, and the gate that fixes it

Appending the JSON-LD `description`/`abstract` whenever it's absent from the output (containment
< 0.6) helps bmcinfectdis (0.07→0.94) and refinery29 (0.28→0.51) but **regresses 3 already-good
docs** (legal-planet 0.94→0.84, asweatlife, thegoodhuman) whose JSON-LD `description` is a
*supplementary blurb* the gold omits. The wins are pages that **under-extracted**; the regressions
are pages that already got the full article. So gate on under-extraction (same idea as the 0091
content-in-links override).

## Fix

After classification, if kept content < 1000 chars AND a long (≥ 500-char) JSON-LD
`description`/`abstract` exists AND it's < 60% already present, append it. The under-extraction gate
excludes well-extracted pages (where the description is just a blurb), so the 3 regressions vanish.

Chosen over the user's "per-site-type thresholds" idea: detecting medical/science reliably is
fuzzy and the global threshold lever is net-negative (0079); this recovers the structured abstract
*only when the page actually under-extracted*, generalizing across academic/medical/news sites with
no domain-guessing and no regressions.

## Results

bmcinfectdis 0.07 → **0.936**; refinery29 0.28 → 0.51. Gate fires on exactly these 2 dev3 docs
(the 3 blanket-append regressors are excluded). dev2 0.8804 flat, dev 0.8917 flat, dev3 0.8859→0.8865. 61 tests pass.
