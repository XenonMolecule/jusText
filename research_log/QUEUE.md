# Work queue (deferred fixes)

Running backlog of fixes/ideas flagged but not yet done. Newest noted as they come up.
See individual `NNNN-*.md` logs for shipped/attempted work.

## Forum (active focus)
- **Forum audit (0042)**: gold reorders username-to-front on 111/1000 dev docs; per-engine
  handlers cover only 29. 58 are "other/unknown" (no engine signature). More engines flagged
  by user: SMF (arduino, adventurecycling), bbPress/WordPress (studiopress), phpBB-variant
  (spacefellowship). Conclusion: build the GENERAL detector.
- **General forum detector** (0041 plan) — repeated user-attributed post blocks → role-to-front;
  reuses `_post_container` + quote-strip. Would ALSO fix the `<ol>` misfire. "Huge win where
  available" (user). Risk: non-forum false fires — needs a strong gate (>=3 user blocks).
- **`<ol>` misfire** (0041 plan) — structural lists (`<ol class="posts"/"d1">`) get numbered
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
- **fastText router** — route pages to the right handler / the general one (needs big_train).

- **Comment recall** — even with comments-on (0034), still missing valuable comments on
  mathematica.stackexchange.com/questions/733 and english.stackexchange.com/questions/19985.
  Check whether hidden/collapsed comments (beyond the displayed `.comment-copy`) are captured;
  the gold may include comments our extractor doesn't reach.

## Formatting / quality
- **Wikia/infobox formatting** — harrypotter.wikia.com/wiki/Tom_Felton?oldid=826898; the gold
  formats the page (infobox/sections) much better than us. Queued.
- **contentdm spacing** — olemiss/cgsc: handled inline-whitespace (0026) but check residual.
- **roseindia code-line join** — `<p>`-per-line code joined with `\n\n` vs gold's `\n`.
- **gist code newlines** (0033) — code outside `<pre>` line-per-div; list half done (0037).

## Methodology
- When out of fix ideas: sample ~5 partial-F1 docs, look for a common error, fix it. This has
  repeatedly surfaced wins we'd deemed impossible (mojibake, spacing, br, emails).
