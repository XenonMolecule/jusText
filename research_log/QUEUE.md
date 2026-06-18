# Work queue (deferred fixes)

Running backlog of fixes/ideas flagged but not yet done. Newest noted as they come up.
See individual `NNNN-*.md` logs for shipped/attempted work.

## Forum (active focus)
- **General forum detector** (0041 plan) — repeated user-attributed post blocks → role-to-front;
  reuses `_post_container` + quote-strip. Would ALSO fix the `<ol>` misfire. "Huge win where
  available" (user). Risk: non-forum false fires — needs a strong gate (>=3 user blocks).
- **`<ol>` misfire** (0041 plan) — structural lists (`<ol class="posts"/"d1">`) get numbered
  when a forum handler misses (forum.wehavelupus.com/showthread.php?9181). Fix via general
  forum detector OR a structural-list exclusion rule.
- **XenForo handler** — attempted (data-author + .messageContent), REVERTED: fired on only
  2/71 train docs and regressed them F1 0.77->0.11 (garbage). Bugs: (1) message-container
  detection wrong — most XenForo skins don't match `[data-author][.//messageContent]` as the
  post block; (2) outermost-dedup direction inverted (kept innermost). Rework: find the real
  per-post container across skins (like `_post_container`), validate on the 71 TRAIN docs as a
  temp dev (user's method -- it correctly caught this breakage).
- **fastText router** — route pages to the right handler / the general one (needs big_train).

## Formatting / quality
- **Wikia/infobox formatting** — harrypotter.wikia.com/wiki/Tom_Felton?oldid=826898; the gold
  formats the page (infobox/sections) much better than us. Queued.
- **contentdm spacing** — olemiss/cgsc: handled inline-whitespace (0026) but check residual.
- **roseindia code-line join** — `<p>`-per-line code joined with `\n\n` vs gold's `\n`.
- **gist code newlines** (0033) — code outside `<pre>` line-per-div; list half done (0037).

## Methodology
- When out of fix ideas: sample ~5 partial-F1 docs, look for a common error, fix it. This has
  repeatedly surfaced wins we'd deemed impossible (mojibake, spacing, br, emails).
