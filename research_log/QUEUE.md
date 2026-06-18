# Work queue (deferred fixes)

Running backlog of fixes/ideas flagged but not yet done. Newest noted as they come up.
See individual `NNNN-*.md` logs for shipped/attempted work.

## Forum (active focus)
- **Forum audit (0042)**: gold reorders username-to-front on 111/1000 dev docs; per-engine
  handlers cover only 29. 58 are "other/unknown" (no engine signature). More engines flagged
  by user: SMF (arduino, adventurecycling), bbPress/WordPress (studiopress), phpBB-variant
  (spacefellowship). Conclusion: build the GENERAL detector.
- **General forum detector** — ATTEMPTED & NEGATIVE (0043): false-fired on 52 non-forum docs
  and regressed -0.34 even on real forums (no clean body selector). Not achievable with
  heuristics. Per-engine handlers remain the only reliable path.
- ~~`<ol>` misfire~~ FIXED (0049, structural-class skip).  (orig: — structural lists (`<ol class="posts"/"d1">`) get numbered
  when a forum handler misses (forum.wehavelupus.com/showthread.php?9181). TRIED a block-aware
  rule (no marker if the <li> contains a block) -- REVERTED: it also broke the gist list,
  whose real items wrap text in <p>. The distinguisher is item SIZE (forum post = huge) not
  block-presence, which SAX can't know upfront. Options left: structural-class denylist
  (posts/nav/d1...; fragile) or, best, just improve forum coverage so these pages are handled
  (bypassing the list logic). Keep 0037 as-is (metric-neutral) until then.
- **XenForo handler** — 4th attempt NEGATIVE (0057). Container detection now SOLVED
  (`*[class~=message][data-author]` fires on 69 train docs, vs 2 before), but body
  `blockquote.messageText` UNDER-extracts (gold 3-4x larger, not just quotes) and the gold
  marker format is inconsistent (talkbass `**user** (date)` vs physicsforums `[user] date`).
  Net F1 -0.020 to -0.026 on the 69-doc temp-dev either quote strategy. STOP unless the
  body-completeness problem is cracked.
- **SMF handler** — SHIPPED (0046).  ~~ ATTEMPTED, defer: usernames+dates extract CORRECTLY across skins
  (arduino: psteve/pYro_65; adventurecycling: SlowAndSlower/staehpj1) via `_post_container` on
  `.poster`+`.post`, but the body (`.post`/`.inner`) includes signatures/"Logged"/quote chrome
  the baseline classifier drops -> regresses -0.05 on 8 dev docs. Needs a tighter body selector
  or per-post classification. Confirms: per-engine handlers only win with a CLEAN body element.
- ~~bbPress~~ SHIPPED (0048): .bbp-reply-content + .bbp-author-name; train +0.0229.
- **vBulletin vB4 broadening** — TRIED & reverted: fixing _strip_quote_blocks to not empty
  blockquote.postcontent bodies made vBulletin fire on vB4 skins (mmo-champion, wehavelupus)
  with CORRECT usernames, but net-negative (general -0.0009, CODE -0.0146): vB4 gold KEEPS the
  quoted text my quote-strip removes (mmo-champion 0.80->0.685). Gold-inconsistency-on-quotes
  wall. Would need a per-doc keep/strip-quotes decision (no clean signal). wehavelupus ol-misfire persists.
- **fastText router** — route pages to the right handler / the general one (needs big_train).

- **Comment recall** — even with comments-on (0034), still missing valuable comments on
  mathematica.stackexchange.com/questions/733 and english.stackexchange.com/questions/19985.
  Check whether hidden/collapsed comments (beyond the displayed `.comment-copy`) are captured;
  the gold may include comments our extractor doesn't reach.

- ~~Table-row cohesion~~ — 0050 NEGATIVE (blanket/digit-gated), then **0051 WIN**: gate on
  row UNIFORMITY (≥8 rows, length-CV ≤0.4, median cell ≤160 chars, ≥2 already kept) keeps
  whole data tables without firing on forum/layout tables. table 0.388→0.710, general
  0.8850→0.8852, zero regression. The classifier was dropping uniform data-table rows at
  random (user-flagged); `merge_uniform_table_rows` fixes it.

## Formatting / quality
- **Wikia/infobox formatting** (source-view markup now stripped, 0045; infobox layout still open) — harrypotter.wikia.com/wiki/Tom_Felton?oldid=826898; the gold
  formats the page (infobox/sections) much better than us. Queued.
- **contentdm spacing** — olemiss/cgsc: handled inline-whitespace (0026) but check residual.
- ~~gist code formatting~~ — SHIPPED (0055): GitHub/gist line-numbered code TABLES rewritten
  to verbatim <pre> (indentation + single-newline preserved; gist Lev 0.679→0.726, aggregate
  flat). 0052's table-row-merge was the wrong tool; the real fix is code-table->pre in preprocess.
- ~~roseindia <code>-block indentation~~ — SHIPPED (0056): multi-line <code> (br-gated) →
  verbatim <pre>, restores &nbsp; indentation (roseindia train Lev 0.873→0.900), aggregate flat.
- ~~general line-per-<p>/<div> code~~ — NOT TRACTABLE (investigated): only ~1 code/dev doc has
  a bare-block code-like run, and a punctuation-ratio code-likeness heuristic FALSE-FIRES on
  prose (flagged elinux headings "Example:"/"Reboot, check modules (lsmod):" as code). No safe
  signal exists without an explicit <pre>/<code>/gutter tag; forcing it would regress prose.
  Code-formatting structures with a clean signal are now all handled: <pre> (0021), code
  tables (0055), <code> blocks (0056).

## Leaked MediaWiki list/indent markup (2026-06-18, investigated — NOT a clean lever)
On `index.php?title=` source/diff-view wiki pages, raw wikitext line-start markup leaks:
`*`/`**` bullets, `:`/`::` indent, `#` numbered (meritbadge `:1. Show`, elinux Peek `* …`,
openwetware `#…`). 0045 strips `[[`/`{{`/`'''`/`==` but not these. Tried stripping leading
`:`/`;` (the subset gold consistently renders): net-negative — fired on only 1 doc and it was
a REGRESSION (applecentral forum −0.0009, where leading `:` is legit "Re:"/quote), negligible
gain on the wiki docs. Gold is inconsistent on the rest too: wikitravel KEEPS `*` bullets;
thejapanesepage/openwetware DROP the bulleted section entirely (content-selection). So no
gold-consistent strip exists. Confirmed gold-typography/content-selection wall.

## Methodology
- When out of fix ideas: sample ~5 partial-F1 docs, look for a common error, fix it. This has
  repeatedly surfaced wins we'd deemed impossible (mojibake, spacing, br, emails).

## Low-Lev band scan (2026-06-18, post-0054)
Scanned 69 high-F1/low-Lev general docs for the most common pred-only short lines. All ruled
out as per-doc, not systemic: `>` lines = email quote-prefixes the gold KEEPS (mailing-list
pages — gold often has MORE `>` lines than us, i.e. we under-extract quotes; gold-inconsistent
so not a clean lever); `none`/`pass` = legit cells in one fedora test-results table;
`- Get more examples` = one oxforddictionaries page. Residual low-Lev is now gold markdown
typography (`**bold**`, `  \n` hard-breaks) + email-quote handling — both prior walls.
Possible future lever: mailing-list quote under-extraction (patchwork gold 84 `>` vs our 22;
ws-policy 129 vs 83) — but gold inconsistency (trauma.org keeps 0) makes it risky.
