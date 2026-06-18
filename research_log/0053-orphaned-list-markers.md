# 0053 — Reattach orphaned list markers

- **Date:** 2026-06-18
- **Tag:** `0053-list-markers`  (baseline: 0051 / 72dcdaf)
- **Status:** landed — quality win, zero regression.

## Bug (found via high-F1 / low-Lev sampling)

Sampling the "Great → Perfect" band (F1 ≥0.85 but Lev <0.78) surfaced **289 orphaned list
markers across 46 dev docs**: a bullet/number sits alone on its own line, split from its item
text — `- \npicking up the spare award` instead of gold's `- Picking Up The Spare Award`.

Cause: when an `<li>`'s text is preceded by a `<br>` (or a leading block), the marker
emission appends `\n- ` and the `<br>` then appends `\n`, so after whitespace-normalization
the merged list paragraph reads `…\n-\nitem…`. The gold always joins `- item` on one line.

## Fix

`fix_orphaned_list_markers(paragraphs)` (post-process): for each non-verbatim paragraph,
`ORPHANED_MARKER_PATTERN` = `(^|\n)(-|\d{1,3}\.)\n(?=\S)` → `\1\2 `. Reattaches a marker that
is alone on a line to the content on the next line. Matches only a line that is *exactly* a
bullet or a 1–3 digit ordered marker followed by a newline + non-space content, so it can't
touch prose.

## Results (0053 vs 0051, all datasets dev)

- All five datasets: F1/Lev **flat to 4 decimals** (whitespace-only change; F1 is token-based).
- Per-doc general Lev: **12 docs changed, net +0.0387**, only one −0.0006 (rounding) —
  mayoclinic +0.024, pawg.cap.gov 0.981→0.985, itninja +0.003, theyworkforyou +0.001.
- 61 tests pass.

Aggregate-neutral but a real readability win with no regression — the data-quality bar
([[data-quality-counts-without-metrics]]).

## Next / not done

- **Cross-paragraph orphans** (e.g. dianerehmshow, 22 markers): the marker is its OWN
  paragraph (the `<li>` content was a block → `_start_new_pragraph` split it off). Reattaching
  needs merging the marker paragraph into the next — the same paragraph-merge that regressed
  peakbagger via the dedup pass in 0052. Deferred; per-paragraph fix is the safe portion.
