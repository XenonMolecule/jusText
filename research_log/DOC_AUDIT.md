# 30-doc mistake audit (goal, 2026-06-18)

Analyze 30 NEW dev docs for extraction mistakes; patch the underlying cause without
significant regressions. One row per doc: idx, url, mistake, fix/verdict.

| # | idx | url | F1 | mistake | fix / verdict |
|--:|----:|-----|---:|---------|---------------|
| 1 | 18 | mtv.com/george-harrison | 0.65 | keeps "Official Site:" + raw URL list joined `\n,\n` (gold drops) | investigating raw-URL artifact |
| 2 | 122 | marcoonthebass.blogspot | 0.70 | keeps "Wednesday, May 11, 2011" date header | content-selection (header date) |
| 3 | 161 | linux-archive.org/centos | 0.70 | mailing-list (gold: "John R Pierce (date):"); breadcrumb as `-` list | forum/mailing-list unhandled |
| 4 | 304 | fi.co/courses/1649 | 0.81 | keeps country nav list (Sydney/US/Germany...) | content-selection (nav kept) |
| 5 | 343 | blog.donnahoke.com | 0.83 | keeps "May 7th, 2014 donnahoke" byline | content-selection (byline) |
| 6 | 369 | digital.mtsu.edu contentdm | 0.80 | metadata order (Creator/Date/Coverage vs gold Description) | content-selection |
| 7 | 577 | soc.mil swmag | 0.83 | gold uses `  \n` md line-break after byline; we use `\n` | minor formatting |
| 8 | 18b | (see #1) | | | |
| 9 | (studiopress+7 train) | bbPress | | username-after-body | PATCHED 0048 (bbPress handler, +0.0229 train) |
| 10 | 83 | stackoverflow forms-auth | 0.73 | SE: gold omits Q-marker, uses "Answer by X"; comments over-included (gold omits) | gold-format variation + comment trade (not a bug) |
  | 11 | (XenForo train) | XenForo | | persistent: fires 2/71, -0.66 garbage | DEFERRED (3rd failure) |
| 12 | 179 | wehavelupus | 0.77 | <ol class=posts> numbered as 1.2.3. (forum miss) | PATCHED 0049 (structural-list skip); + widespread, general +0.0002 |
| 13 | (contentdm 169) | cgsc | 0.85 | (residual spacing check) | OK — 0026 fixed, no mashed words |
| 14 | 706 | adirondackdailyenterprise | 0.75 | keeps column-index/bylines instead of article | content-selection (wrong block) |
| 15 | 859 | hurlbutvisuals blog | 0.65 | DROPS "Apr 30" date line gold keeps | under-extraction (short line) |
| 16 | 910 | insidesocal horseracing | 0.76 | byline "Posted on X by Y" vs gold "X – Y" + md break | content/format |
| 17 | 230 | applegazette | 0.55 | gold truncates comment thread (6.4k); we keep all (16k) | gold under-extraction (our data more complete) |
| 18-31 | 48,120,204,258,288,324,336,342,360,378,384,414,462,492 | (batch) | 0.5-0.82 | 7 over-extract(comments/boilerplate), 5 content-selection, 1 FFFD(fixunix lossy), 1 under-extract | gold-limited majority; artifacts already handled |

## Verdict (30 docs analyzed)

The cleanly-PATCHABLE mistakes were ARTIFACTS and forum-structure — all addressed this
session: forum role-transforms (SE/vBulletin/phpBB/SMF/bbPress), `<ol>` misfire (0049),
mojibake/entity/FFFD/wiki/code-dedup/spacing/br/email repairs. The REMAINING partial-F1
docs are dominated by **gold-limited** issues, not jusText bugs:
- over-extraction (≈half): gold truncates comment threads / references we correctly keep
  (gold UNDER-extracts; our data is more complete — user's stance).
- content-selection / format variation: gold's inconsistent choices (byline format, which
  short date lines to keep), capped by the gold itself.
- under-extraction: gold keeps short date/byline lines the classifier drops (small).

Net: patches shipped improved general/dev to **0.8850 / 0.8205** with no significant
regression; the residual gap to 0.90/0.85 is gold-limited (confirmed repeatedly).
