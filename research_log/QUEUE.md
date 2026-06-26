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
- **XenForo handler** — SHIPPED (0058, reverses 0057). The 0057 "body under-extracts"
  diagnosis was wrong: `blockquote.messageText` → `ParagraphMaker` captures the full body;
  the real missing piece was the **time** (in the `.DateTime` `title` attr, not the visible
  text). With time recovery + strip-quotes it's train +0.74 F1 / +1.11 Lev (39 wins), dev
  +0.23, general dev +0.0002/+0.0004, 4 datasets flat. One known loss: howtoforge
  pasted-logs-in-quote (gold keeps; not cheaply gateable).
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
- ~~Wikia/infobox formatting~~ — NOT a clean lever (investigated): gold formats infoboxes as
  `- **Key:** Value` (markdown bold-key list) on only 2/12 dev infobox docs (harrypotter,
  wikipedia/Berkovitsa) — rare AND requires replicating markdown bold, which is gold-
  unpredictable (0024). The label:value pairing is structural but without the bold won't
  match gold. Gold-typography wall.
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

## dev2 spot-check batch (2026-06-25, user-flagged — diagnosed, not yet fixed)
All four are in `datasets_rawhtml/general/dev2`, scored with `general-ftstack`. Two are clean-fix
candidates; two are the known low-stopword recall wall.

- **slysa.org** (`com_community` JomSocial/SP Page Builder, F1 0.869) — **CANDIDATE (over-extraction
  cleanup)**. Leaks orphan UI-label paragraphs: two `By` (from dead `sp-tweet` Twitter widgets whose
  message/author/date are JS-injected → hollow in the snapshot, only the template word "By" survives)
  + `Full Story` (an `sp-readmore` link between showcase title and body). Scan: **7 dev2 docs** emit a
  bare label-only paragraph (`By`/`by`/`Author`/`Share`/`Read More`/`Full Story`): plantengineering,
  defenseone, allaboutjazz, call-cc wiki, accesstoinsight, theoutbound, slysa. Proposed fix: drop a
  kept paragraph whose entire text is a single known UI label. Low risk (these are never gold content).
  Secondary leaks (poll widget, missing `...` on JS-truncated previews) are JS-render artifacts — skip.
- **hub.hku.hk/handle/10722/231252** (DSpace repository, F1 0.872) — **CANDIDATE (under-extraction,
  user priority)**. Drops the `Authors: NIU, Y; Lu, W; LIU, D; CHEN, K` metadata row. Authors are
  `<a class="author">` links in the DSpace `ds-` item-view table (also present as `DC.creator` /
  `citation_author` metas); gold joins them "Authors: a; b; c". The metadata table (Authors / Issue
  Date / Citation) is dropped as link-dense/low-stopword. Proposed fix: a DSpace item-view handler
  (recognizable platform, like the forum engines) that emits the labeled metadata rows. Worth a real try.
- **drive.com.au/motor-news/land-rover…** (F1 0.870, nHTML=4 multi-doc) — **RECALL WALL**. Missing a
  price table rendered WITHOUT `<table>` (no table elements): `TD4 (Man) $44,990 / XS I6 $49,990 / …`.
  Short low-stopword model→price lines dropped by the classifier. Same class as cji/monroe/all-science.
- **cji.edu/…/methamphetamine-awareness** (F1 0.884) — **RECALL/DEDUP WALL**. Drops half the
  `Registration ends 12pm (noon) <Month> <day>, 2017` lines (and whole Oct/Nov sessions). They're
  near-identical template text (low-stopword, repetitive) so the classifier reads them as boilerplate —
  but the unique date each carries is the information-dense part. No clean signal separates "repeated
  chrome" from "repeated template wrapping unique data"; same wall as the threshold/heuristic levers
  (research_log 0079, both NEGATIVE).

## More user-flagged docs (2026-06-25, batch 2)
- **ask.metafilter.com/233299** — parses well already, but user prefers the **commenter name
  before the comment** (role-transform like the forum engines). User also likes that the
  **favorites count** and metadata are kept — so the fix is reorder-to-front, NOT dropping the
  numbers. MetaFilter/AskMe is its own engine (`.comments`, commenter in a byline). Candidate
  role-transform handler; check the gold actually fronts the commenter before building.
- **sauer-thompson.com/archives/opinion/2012/12/a-downbeat-nati.php** — missing **comment
  attribution** (who said each comment), "pretty critically important" per user. Movable Type /
  blog comment thread; check `_comment_author_meta`/`prepend_comment_authors` coverage (0068/0070)
  — the commenter byline may be in a structure those selectors miss.

## More user-flagged docs (2026-06-25, batch 3)
- **leanpub.com/pythontesting/read** — partial table-of-contents with rows **selectively dropped**.
  User: "if we are going to include a part of a TOC it is really bad to start dropping rows
  selectively." Same selective-drop pathology as the cji dates / drive price-table (classifier
  keeps some near-uniform list rows, drops others). All-or-nothing for a TOC would be better.
  Possibly addressable via `merge_uniform_table_rows`-style cohesion (0051) applied to TOC `<li>`
  lists. Check structure.
- **thejournal.com / pajcisenate.org** — SPACING (in progress, research log 0083): words glued at
  inline-element boundaries (`Enhancing<img>Education`) and adjacent block elements not in the
  paragraph/separator tag sets (`<address>` contact blocks → `TreasurerJulia`). NB some gluing is
  in the raw source (thejournal `BehindAct`/`aswell` — print-to-HTML artifact, gold fixed from
  context, unrecoverable).

## Metafilter engine handler (2026-06-25, DESIGNED, ready to build)
ask.metafilter.com / metafilter.com — 1 dev2 + 4 train docs. Gold puts the **commenter to the
front** (matches user preference): `**username** (TIME, DATE):` before each comment, with a `---`
separator after the question. Current F1 0.891 (233299).
- **Structure:** title from `h1` (strip trailing "January 16, 2013 2:50 PM Subscribe"); question
  body from `div.copy` (not `.smallcopy`); each comment is a `div.comments` whose trailing
  `span.smallcopy` byline is `posted by <user> at <TIME> on <DATE> [N favorite(s)]`. Skip the
  nav div (`« Older … |`) and the "This thread is closed to new comments." div.
- **Byline parse:** `posted by (.+?) at (.+?) on (.+?)(?: \[(\d+) favorite)?` → user/time/date/favs.
- **USER DECISION (recorded):** KEEP favorites (quality over metric) — the gold drops them, so
  appending `[N favorites]` to the marker will slightly regress F1/Lev on the 5 metafilter docs.
  This is an authorized exception to no-regression, scoped to metafilter only. Marker form:
  `**user** (TIME, DATE) [N favorites]:`.
- **Build like the forum engines** (own meta reader, NOT `_forum_thread_paragraphs` — question has
  no author marker + there's a `---` separator). Prototype offline vs all 5 docs first; gate tightly
  on the `posted by … at … on …` byline so nothing else fires. Verify dev/train aggregate stays
  ~flat (5 docs × small regression = negligible) and NO non-metafilter doc moves.

## dev3 survey (2026-06-25) — baseline F1 0.8821 / Lev 0.8203 (2000 docs, 2013-2022 snapshots)
Fresh random sample, disjoint from all other splits. Baseline is in line with dev2 (0.8804) —
the fork generalizes well; modern JS frameworks are NOT a major failure mode.
- **Framework prevalence:** React 15 (4 bad), Angular 35 (3), Vue 5 (0), Ember 86 (7),
  JS-state-blob 203 (16). SPAs are a minority and mostly the already-detected JSON-blob case (0075).
- **CONTENTdm digital libraries (INVESTIGATED — recoverable but heterogeneous):** content is in
  `window.__INITIAL_STATE__ = JSON.parse('…')` (JS-escaped JSON; decode via
  `m.group(1).encode().decode('unicode_escape')` then `json.loads`), NOT the DOM. But the gold's
  source FIELD differs per page type:
  - `item.item.text` (OCR full text): westlakelibrary gold≈text → emit gives **0.00→0.99**;
    uidaho gold is a clean PREFIX of a 49k OCR (gold truncated the long newspaper) → full-text
    emit only 0.19, prefix 0.98 (can't replicate the cut point).
  - `collection.pageText` (collection landing HTML, needs tag-strip): augie.
  - item `fields[0].value` (Title) + short `item.item.text` (caption): digitalhorizons (a photo).
  A handler needs 3 branches (item-OCR / collection-landing / item-metadata) + the uidaho
  gold-truncation is a wall. Clean slice = item-OCR-text branch (westlake clean, uidaho partial).
  Only ~4 dev3 docs; check train/test CONTENTdm count before investing in all branches.
- **Encoding (U+FFFD) is upstream, NOT jusText:** 131/2000 dev3 docs carry baked-in U+FFFD from the
  WARC→raw_html decode step (decoding bytes as UTF-8 + errors=replace, ignoring the declared/HTTP
  charset — comune.napoli.it even declares ISO-8859-1 and was still corrupted). Unrecoverable once
  baked in. Fix is in the extraction pipeline per WARC-decoding-recommendations.md (w3lib
  html_to_unicode, windows-1252 fallback, drop errors=replace). Not a jusText cycle.
- Other worst docs: naver.com Korean dict (tiny gold, foreign), yammer (gold≫html, JS/login wall),
  weatherbug/brighttalk (JS), several wordpress tag/author listing pages (queenslib, gonzotown —
  listing-page over/under-extraction). Triage in a later cycle.

## JS-blob under-extraction — triaged NEGATIVE (2026-06-25)
Hypothesis: the 203 dev3 `__INITIAL_STATE__`/state-blob docs are a systematic recoverable category
(like CONTENTdm 0087). Triage says NO:
- **JSON-LD `articleBody`**: only 17 dev3 docs have it (≥200 chars); 16 already score F1≥0.6 (a site
  emitting articleBody almost always renders the DOM too, so it's redundant). Exactly 1 doc would
  improve (dogtrickacademy forum 0.37→0.65, and it's mediocre). Building it risks regressing the 16
  good docs. NOT WORTH IT. **Containment-gated refinement** (use articleBody only when its tokens
  are <60% present in the DOM extraction — self-correcting like remerge): fires on 0/17 docs,
  +0.0000. Reason: all 17 already have the article in the DOM (containment high); dogtrickacademy's
  DOM has the article too, just buried in over-extraction (an OVER-extraction/precision issue, not
  under-extraction). articleBody is definitively closed as an under-extraction lever.
- **Long-link unwrap** (content-in-`<a>`, hqnetwork): recovers hqnetwork 0.00→0.79-1.00 but
  regresses dev2 −0.0047 to −0.0061 at every word threshold (re-admits related/nav/directory link
  blocks the gold drops). Net-negative recall lever, same wall as the 0079 threshold/heuristic
  levers. NOT SHIPPED.
- The genuinely-stuck JS-blob docs (~16, F1<0.5) use heterogeneous custom schemas (window.__,
  bespoke application/json) — per-site one-offs, no shared key. Low ROI. CONTENTdm (0087) was the
  one platform worth a handler because it had 4 docs + a stable `collectionAlias` signature.

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

## Robustness: NULL bytes / control chars crash the extractor (2026-06-26, queued)
A doc with NULL bytes or other control characters crashes jusText -- lxml raises
"All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters".
Should be handled gracefully (strip/sanitize control chars in html_to_dom before parsing, like the
empty-HTML guard 'Handle empty/unparseable HTML gracefully'), so one bad doc never crashes a batch.
Fix: in html_to_dom, drop disallowed control chars (keep \t \n \r) from the text before lxml parse;
catch lxml.etree.ParserError/ValueError and fall back to an empty doc.

## Table rendering follow-ups (2026-06-26, user-flagged during th-gate work)
The `<th>`-gated pipe rewrite (rewrite_data_tables) handles clean uniform header tables (TSA,
calendar w/ &nbsp; empty cells, patents, Wikipedia Film table). Open gaps the user flagged:
- **Ragged tables skipped wholesale** — Wikipedia *Rebecca Balding* has two filmography tables; the
  Film table pipes, the **Television table does NOT** (one row has a different column count from
  colspan/rowspan, so `len(widths)!=1` kills the whole table). Need to tolerate a ragged row
  (pad/normalize columns) instead of skipping. Also that doc shows a **title-duplication** artifact
  ("Boogens, TheThe Boogens" = sort-key span + display title concatenated) and **truncation**.
- **atsdr.cdc.gov/HAC/pha/pha.asp?docid=873&pg=2** — contaminant data tables get **mangled/truncated**:
  the classifier splits cells into separate paragraphs and DROPS values (gold has clean
  `| Contaminant | Max Conc | Comparison | Source |`). th-gate didn't fire (likely ragged or cell
  >80 chars) AND the row-dropping (0051 should keep all rows) failed. High-value: real data lost.
- **pfam.janelia.org/family/PF14029** — a label-value block where every line ends in `:`
  ("Seed source: …", "Type: Family", "Number in seed: 53") is double-newlined; should be
  single-newlined (the colon→single-newline rule, but this may be a `<dl>`/`<p>` list, NOT a
  `<table>`, so rewrite_data_tables won't see it — extend the colon-collapse to dl/p runs).

## #2 — Narrow ragged DATA-table handling (shipped 0099 reverted broad ragged)
The uniform-width gate skips ragged tables. Two flavours of ragged table the gold DOES want piped:
- **Multi-section** (atsdr docid=873 table-2): colspan section-header rows ("Organics"/"Inorganics")
  split one <table> into sub-tables of different widths. Want: split at 1-cell rows → independent
  per-section pipe tables (each its own width + `--- | ---`).
- **Multi-level header** (genomebiology gb-2006-7-6-r47 Table 2): colcounts [2,4,10], th header rows
  then uniform 10-col td data, 59% numeric. Classifier currently dumps every cell on its own line.
  NOTE: the gold here is itself wrong (collapsed 9 data cols → 3, mislabeled Clone 5's three
  order-values as Clone 5/6/18) — so a perfect fix won't fully score; quality call.
KEY discriminator vs the forums/forms that broad ragged ruined: **numeric/short-cell density + <th>
header + low link density**. Forums ≈0% numeric, long text cells, many links → still skipped.
Gate a ragged rewrite on e.g. ≥30% numeric cells AND <th> header AND existing link/length/empty
gates. Verify on: atsdr, genomebiology (fire) vs psypokes, paia, UniProt-features (skip).
