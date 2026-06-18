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
- **XenForo handler** — attempted (data-author + .messageContent), REVERTED: fired on only
  2/71 train docs and regressed them F1 0.77->0.11 (garbage). Bugs: (1) message-container
  detection wrong — most XenForo skins don't match `[data-author][.//messageContent]` as the
  post block; (2) outermost-dedup direction inverted (kept innermost). Rework: find the real
  per-post container across skins (like `_post_container`), validate on the 71 TRAIN docs as a
  temp dev (user's method -- it correctly caught this breakage).
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
- ~~roseindia / gist code-line join~~ — CLOSED (0052 NEGATIVE): merging kept table/code rows
  into one `\n`-joined block has no Lev upside (Exeter cell-separators are U+202F gold-
  typography; gist doesn't qualify + loses indentation upstream) and regressed peakbagger
  −0.13 via the dedup interaction. roseindia/dev is over-extraction (Q&A), not newline. The
  tractable half (keep the rows) shipped in 0051.

## Methodology
- When out of fix ideas: sample ~5 partial-F1 docs, look for a common error, fix it. This has
  repeatedly surfaced wins we'd deemed impossible (mojibake, spacing, br, emails).
