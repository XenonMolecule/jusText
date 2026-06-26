# 0100 — Ragged data tables (numeric-gated) + display:none-in-tables fix

Follow-up to 0099. Two things: (1) fix the UniProt ``<p>`` leak that 0099's cell-local strip missed,
(2) handle the *ragged* data tables 0099 deliberately deferred.

## display:none inside data tables (fix to 0099)
0099 added ``_clean_cell_text`` to drop ``display:none`` tooltips from table cells, but it ran inside
``rewrite_data_tables`` — *after* ``preprocessor``'s ``Cleaner(style=True)`` had already stripped the
``style=`` attribute, so it matched nothing (no-op). UniProt's escaped ``<p>`` help markup still
leaked into the piped feature table. Moved the strip into ``preprocessor`` (before Cleaner), scoped
to ``table[.//th]`` (the data tables we pipe). NOT all ``//table``: stripping hidden content from
*layout* tables removes text the raw-HTML gold keeps (−0.0004 dev3 for all-tables; −0.0056 dev2 for a
global strip). Tail-preserving via ``_drop_keep_tail`` (keeps "Active site", the hidden span's tail).

## Ragged data tables (the #2 deferred from 0099)
A genuine data table can be ragged: a multi-section table with colspan section-header rows (atsdr
``docid=873`` Organics/Inorganics) or a multi-level colspan header (genomebiology ``gb-2006-7-6-r47``
Table 2, cols [2,4,10]). 0099's uniform-width gate skipped these → the classifier mangled/truncated
them (each cell its own line). 0099's *broad* ragged tolerance fixed them but **false-fired on forum
layout tables** (psypokes, paia) — reverted.

Discriminator (measured): for ragged tables, **numeric cell density** cleanly separates data from
layout. atsdr-2 = 46 %, genomebiology-2 = 70 %; psypokes/paia forums = **0 %**. So the ragged path
fires only when: ragged + a ``<th>`` header row + ``_numeric_frac ≥ 0.30`` + the shared link/median/
empty gates + **not a calendar**. Render: pad rows to the max width (first-cell-only ``&nbsp;``),
1-cell colspan rows → section-label lines, ``--- | ---`` after the first all-``<th>`` row. All data
survives as a ``<pre>``.

Imperfect by nature: a multi-level header flattens (genomebiology's "5 6 18" / "0th 1st 2nd" become
two header rows), and the genomebiology *gold* is itself wrong (collapsed 9 data cols → 3). The win
is **no data loss** on real scientific/data tables, at the cost the gold's own inconsistency imposes.

## Calendars (the regression that nearly sank it)
The first ragged cut was −0.0003 dev3: a per-doc diff showed **100 % of the regressions were blog
month-calendar widgets** (the colspan "December 2017" caption makes them ragged, day numbers give
high numeric density). The gold drops them as boilerplate; the ragged path rescued them into a
``<pre>``. ``_is_calendar`` excludes them, by two signals: a day-of-week header row (English names),
*and* a language-independent structural test — a ~7-wide grid that is ≥70 % day-of-month integers
(1-31) — which catches German/Italian/etc. calendars the name list misses. Genuine *content*
calendars (newenglandfilm) are uniform, take the uniform path, and are untouched.

## Results
dev2 0.8803→**0.8804** (+0.0001), dev3 0.8867→**0.8867** (flat). Per-doc dev3 diff vs baseline: 4
docs change, the two worst are −0.003/−0.002 on patent-application tables (gold inconsistency), two
improve (+0.012 Wikipedia). Flagged-doc harness (``benchmark/eval/check_flagged.py``): ALL PASS —
forums un-piped (0 % numeric), UniProt table clean, TSA F1=0.994, calendars dropped,
atsdr/genomebiology now pipe with every value preserved.
