# 0045 — Strip unrendered MediaWiki markup

- **Date:** 2026-06-18
- **Tag:** `0045-wiki`
- **Status:** landed — quality win (cleaner wiki text), zero regression.

## Idea (found via partial-F1 sampling)

Sampling mid-F1 dev docs (user's method) surfaced meritbadge.org/wiki with **raw MediaWiki
markup** in the output: `[[Athlete |Webelos Activity Badge]]`, `{{...}}`, `'''bold'''`,
`== headings ==`. 17 dev docs (`index.php?title=` wiki source views: panotools, wikitravel
with 60 markup hits, fedora, …) leak unrendered wikitext that the gold renders to clean text.

## Fix

`clean_wiki_markup` strips, per non-verbatim text node that contains `[[` or `{{`:
`{{templates}}` (removed, nested), `[[a|b]]`→`b` / `[[a]]`→`a`, `[url text]`→`text`,
`'''/''` bold/italic, `== heading ==`→`heading`. Gated on `[[`/`{{` so prose with stray
apostrophes is untouched (an earlier `''`-triggered version regressed 1 doc). Runs under
`fix_encoding`.

## Results

- 17 dev docs with wiki markup: F1 **0.7033 → 0.7098 (+0.0065)**, Lev **0.5391 → 0.5531
  (+0.0141)**; markup fully removed (meritbadge `[[` 10→0).
- general/dev **0.8850 flat** (Lev 0.8201→0.8202); domains flat; 61 tests pass.

Aggregate-neutral (17/1000) but a real readability win with no regression — the data-quality
bar. Addresses the queued wikia-formatting concern for source-view wiki pages.
