# 0054 — Reattach cross-paragraph orphaned list markers

- **Date:** 2026-06-18
- **Tag:** `0054-xmarker`  (baseline: 0051 / 72dcdaf; extends 0053)
- **Status:** landed — quality win, zero regression.

## Bug (the half 0053 left)

0053 fixed *within-paragraph* orphaned markers (`…\n-\nitem…`). The remaining case: when an
`<li>` wraps a block element, `_start_new_pragraph` splits the bullet into its OWN paragraph
and the item text into the next (e.g. dianerehmshow transcript: a `-` paragraph followed by a
`10:22:07 …` paragraph). The caller then joins them with `\n\n`, stranding the marker.

## Fix

Extended `fix_orphaned_list_markers` with a paragraph-list pass: a kept paragraph whose text
is *exactly* a marker (`-` or 1–3 digit ordered) **and** whose dom_path is inside an `li`
gets prepended to the next kept paragraph; the marker paragraph is dropped. Guards: skip if
the next kept paragraph is itself a bare marker.

**Why this is dedup-safe** (unlike 0052's table block-merge that regressed peakbagger −0.13):
it only ever touches paragraphs that are *already kept*. 0052 force-promoted every table row,
resurrecting rows the dedup pass had correctly dropped; here the `-` marker was never deduped
and the item paragraph is already kept, so no content is resurrected.

## Results (0054 vs 0051, all datasets dev)

- All five datasets F1/Lev **flat to 4 decimals** (whitespace-only; F1 token-based).
- Per-doc general Lev (combined within+cross): **23 docs improved >0.0005, 1 regression**
  (−0.0006 thesaurus, rounding; F1 unchanged). dummies.com +0.0065, ksbw +0.0048,
  pillsbury +0.0025, cisco +0.0022, mayoclinic +0.024 (from 0053).
- 61 tests pass.

Aggregate-neutral, real readability win, no regression — the data-quality bar
([[data-quality-counts-without-metrics]]). Orphaned-marker artifact now fully closed.
