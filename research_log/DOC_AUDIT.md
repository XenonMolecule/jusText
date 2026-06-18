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
