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
