# Research log

Chronological record of jusText experiments on the extraction benchmark. One file
per idea/version, newest insights captured while fresh. **Keep each entry under a
5-minute read.**

## Convention

- Files: `NNNN-short-slug.md` (zero-padded, monotonically increasing).
- Every entry names the jusText **run tag** it was measured with (`vX.Y.Z-<sha>`),
  so results trace back to cached runs under `benchmark/runs/<tag>/`.
- Compare against the previous version with `viz.py compare <prevTag> <thisTag>`.

## Iteration cycle

Each cycle is one pass of the loop below. A "cycle" maps to roughly one research log
entry and one commit — though a single hypothesis may take several un-committed edits
before it earns a commit.

1. **Backfill** — add the git commit id to the *previous* entry (now that it exists).
2. **Review** — skim prior entries; note anything to revisit or that informs today.
3. **Preregister** — write the hypothesis for this cycle *before* coding (a stub
   entry with Hypothesis filled in). Hypotheses are often engineering fixes.
4. **Revert (rare)** — if a past change should be undone, `git revert`/reset to the
   right commit first. Usually skipped.
5. **Change** — make the code changes to test the hypothesis.
6. **Measure** — run train/dev (`run_eval.py --tag <new>`); never test mid-cycle.
7. **Iterate** — refine and re-run freely. Multiple edits per hypothesis is fine and
   expected; not every edit is a commit.
8. **Log** — once the benchmark moves meaningfully (or the idea is ruled out), fill in
   the entry: Results (vs. prior tag via `viz.py compare`), Insights, Next.
9. **Commit** — commit the code + log entry together.
10. **Repeat.**

Guardrails: test split stays vaulted until milestones (`--allow-test`). Tune on
train/dev only. Domain splits are tiny — trust direction, not decimals.

## Entry template

```markdown
# NNNN — <title>

- **Date:** YYYY-MM-DD
- **Tag:** vX.Y.Z-<sha>   (baseline compared against: <prevTag>)
- **Status:** idea | in progress | landed | abandoned

## Hypothesis
One or two sentences: what we believe is wrong and what change should help.

## What changed
Bullet points of the actual code/heuristic change.

## Results
Small table vs. the comparison tag (dev/train; test only at milestones).
Net effect in one line.

## Insights
- What we learned (whether or not it worked). Failure modes confirmed/ruled out.

## Next
- Concrete follow-ups this surfaced.
```

## Index

general/dev F1: 0.762 (baseline) → 0.849 (0009) → 0.870 (0016 fastText) → **0.876** (0018 +dedup). Lev: 0.682 → **0.808**.
**Current best (ftstack + quality/transform fixes 0021-0031):** general dev **0.886/0.821** | code 0.842 | science 0.989 | math 0.820 | table 0.388*. Target 0.90/0.85.  (*table/math 2-doc noise)
table/dev: 0.0 → **0.449** (0009).

- [0001 — Baseline (jusText v3.0.2)](0001-baseline.md) — general 0.762/0.682
- [0002 — Relax good-anchor thresholds](0002-relax-good-anchor-thresholds.md) — **+0.047** (recall fix)
- [0003 — Learned RandomForest classifier](0003-learned-paragraph-classifier.md) — **+0.034** (opt-in model)
- [0004 — Labels (neg) + DOM features](0004-labels-and-dom-features.md) — +0.004; table +0.15
- [0005 — Threshold sweep (negative)](0005-threshold-and-plateau.md) — 0.5 optimal
- [0006 — Failure-taxonomy tool + ceiling](0006-failure-taxonomy-and-ceiling.md) — oracle 0.893
- [0007 — Content features (negative, reverted)](0007-code-math-content-features.md)
- [0008 — Code/math deep-dive](0008-code-math-deepdive.md) — text-stack +0.0035 (not shipped, runtime)
- [0009 — Stop fragmenting rows/lists](0009-row-list-segmentation.md) — **table +0.24**, raised oracle 0.893→0.902
- [0010 — Post-breakthrough sweep (negatives)](0010-post-breakthrough-sweep.md) — threshold/forms/language/separator not levers
- [0011–0013 — text-stack experiments](0013-fuzzy-text-stack.md) — fuzzy label (oracle 0.944), sklearn stack
- [0014–0015 — ceiling + failure deep-dive II](0015-failure-deepdive-2.md) — precision leak is context-dependent
- [0016 — fastText-on-100k stack](0016-fasttext-100k-stack.md) — general 0.870/0.801, +data breakthrough
- [0017 — math deep-dive](0017-math-deepdive-plan.md) — LaTeX-keep NEGATIVE; math-image detector; gold drops image-math
- [0018 — paragraph dedup](0018-dedup.md) — general 0.876/0.808 (+0.006/+0.007, additive)
- [0019 — neighbour fastText-prob](0019-neighbor-ftprob.md) — **BEST: general 0.880/0.814** (boundary signal)
- [0021 — verbatim code indentation](0021-pre-whitespace.md) — preserve `<pre>`/`<textarea>` whitespace (quality)
- [0022 — mojibake repair](0022-mojibake-repair.md) — signature-gated ftfy fix, quality win, zero regression
- [0023 — double-entity decode](0023-double-entities.md) — unescape double-encoded entities, quality win, zero regression
- [0024 — markdown trigger classifier](0024-markdown-trigger.md) — NEGATIVE: gold bolding unpredictable (per-doc & per-span both learn "never bold")
- [0025 — <br> → newline](0025-br-newline.md) — line structure for <br>-separated content; F1-neutral, Lev net-positive (quality)
- [0026 — inline whitespace](0026-inline-whitespace.md) — keep space between inline elements; **general +0.0022 F1** + fixes mashed words
- [0027 — angle-bracket emails](0027-angle-emails.md) — escape `<addr@host>` libxml2 ate as a tag; **forum +0.22 F1**, zero regression
- [0028 — PLANNED forum quotes](0028-PLAN-forum-quotes.md) — reply-quote dedup (deprioritized: jusText > gold on the shared example)
- [0029 — U+FFFD repair table](0029-fffd-repair.md) — context→char infill for replacement chars; quality fix, zero regression
- [0030 — dedup quote-normalize + containment](0030-dedup-quotes-containment.md) — **general +0.0005 F1 / +0.0006 Lev**; kills encoding-variant & teaser dupes
- 0031–0049 — quality/transform fixes & forum role-transforms (see individual files): mojibake/entity/FFFD/wiki/code-dedup/spacing/br/email repairs; forum engines SE/vBulletin/phpBB/SMF/bbPress; `<ol>` structural-skip (0049). General/dev → **0.8850 / 0.8205**.
- [0050 — table-row cohesion](0050-table-row-cohesion.md) — **NEGATIVE**: blanket/digit-gated row cohesion regresses real general docs
- [0051 — uniform data-table rows](0051-uniform-table-rows.md) — **WIN**: keep whole table when rows are uniform (≥8, low length-CV, short cells) & some kept; **table 0.388→0.710, general 0.8850→0.8852, zero regression**
- [0052 — code/table newline join](0052-code-newline-join.md) — **NEGATIVE**: re-joining kept rows into a `\n`-block has no Lev upside (U+202F gold cell-typography) and regressed peakbagger −0.13 via dedup; reverted
- [0053 — reattach orphaned list markers](0053-orphaned-list-markers.md) — **quality win**: bullet/number split from its item text by a `<br>` (within-paragraph); per-doc general Lev net +0.039
- [0054 — cross-paragraph orphaned markers](0054-cross-paragraph-markers.md) — **quality win**: marker as its own paragraph (li-wraps-block) prepended to next kept para; dedup-safe; 23 general docs improved, 1 trivial regression
- [0055 — code tables → <pre>](0055-code-table-pre.md) — **code-formatting win**: GitHub/gist line-numbered code tables → verbatim <pre>; indentation+single-newline (gist Lev 0.679→0.726), aggregate flat
- [0056 — code blocks → <pre>](0056-code-block-pre.md) — **code-formatting win**: multi-line <code> (br-gated) → verbatim <pre>, restores &nbsp; indentation (roseindia Lev 0.873→0.900); aggregate flat, no real regression
- [0057 — XenForo 4th attempt](0057-xenforo-4th-attempt.md) — **NEGATIVE**: container detection solved (fires 69 train docs) but body under-extracts 3-4x + gold marker format inconsistent; net −0.02 F1, not shipped
- [0058 — XenForo SHIPPED](0058-xenforo-shipped.md) — **reverses 0057**: title-attr time recovery + full `blockquote.messageText` body flips it to train +0.74 F1 (39 wins); user-flagged droidforums k9 thread 0.934→0.994; general dev +0.0002/+0.0004, 4 datasets flat; strip-quotes (keep craters −1.6)
- [0059 — SE accepted-answer flag](0059-se-accepted-flag.md) — **quality signal (user opt-in)**: accepted answer already retained; flag `(accepted)` on multi-answer threads only; gold-inconsistent (44/101) so net ~0 full-dataset (general flat), a chosen signal not a gold-match
- [0060 — vBulletin first non-empty username](0060-vbulletin-empty-username.md) — **bug fix**: empty avatar `<a class="username">` made `users[0]` blank → handler skipped every post (androidcentral); take first non-empty username; that doc 0.929→0.983, exactly 1 doc changes, zero regression
- [0061 — collapse source-text newlines](0061-source-newline-collapse.md) — **Lev quality win**: pretty-print/wrapped-prose newlines in text nodes were surviving as line breaks (recipe `<dl>` ingredient quantity split from name); collapse source `\n` to space, keep only `<br>`/marker-injected `\n`; general Lev +0.00069, code +0.00103, science +0.00357, F1 flat
- [0062 — drop doubled list numbers](0062-doubled-list-numbers.md) — **quality win**: recipe steps with an explicit source number doubled our injected `<ol>` marker (`2. 2 In large bowl`); strip the source number when doubling is systematic (≥2 items, ordinal-matched); pillsbury 0.950→0.956, exactly 1 doc changes, zero regression
- [0063 — vBulletin4 postcontent wrapper](0063-vbulletin-postcontent.md) — **big win**: `_strip_quote_blocks` deleted the vB4 `blockquote.postcontent` body wrapper → handler fell through on the whole vB4 install base; exclude postcontent from the strip; general +0.0008/+0.0010, code +0.0047/+0.0062, 227 forum docs ΣΔF1 +3.67
- [0064 — skip style/script text](0064-style-script-skip.md) — **quality fix**: forum handlers run ParagraphMaker on raw DOM (pre-preprocessor), so inline `<style>` leaked CSS as text (mathhelpforum equations → `img.top {vertical-align:15%;}`); ParagraphMaker now drops `<style>`/`<script>` text; that doc 0.46→0.55, dev flat
- [0065 — recover LaTeX math images](0065-latex-image-recovery.md) — **quality win**: math forums render equations as `<img>` from a LaTeX renderer (codecogs/mimetex) with formula in `alt`/`src`; transcribe to plaintext (`\frac 1{4-y}`→`1/(4-y)`) like the gold; train +0.96 F1 over 11 docs (67637 0.55→0.81), dev flat (0 dev docs)
- [0066 — restructure FAQ accordions](0066-faq-restructure.md) — **quality win**: off-canvas FAQ lists questions twice (trigger `ul.questions` + real `div.faq` Q/A); dedup kept the trigger and orphaned answers; drop the trigger + per-block chrome, gated on ≥2 faq blocks; oshidefender 0.912→0.974, exactly 1 doc changes, zero regression
- [0068 — highlight blog-comment authors](0068-comment-author-highlight.md) — **quality fix (user-prioritised)**: WordPress comments kept the body but dropped the author; post-classification prepend `*author* (date):` to already-kept comments only (no resurrection); fixes `Permalink`-as-author + pingback bugs; SAP 0.962→0.979, full-dev −0.00006 F1
- [0070 — comment author on its own line](0070-comment-author-line.md) — **placement fix (0068)**: 0068 inline-skipped short greetings (`Hi Krishna,`) so the marker landed on line 2; now insert `*author* (date):` as its own paragraph before the first kept line, matching gold; SAP 0.9787→0.9797, dev neutral
- [0071 — workitmom Drupal forum](0071-workitmom-forum.md) — **forum role-transform**: custom Drupal group thread (li[id^=post_], div.body, ".comment-by: Posted by X on DATE") had no handler → missing markers + dropped first post; gated handler; that doc 0.817→0.942, exactly 1 doc, zero regression
- [0072 — phpBB date-before-author + leak](0072-phpbb-date-leak.md) — **phpBB fix**: WP-integrated skins put the date before "by author" (regex missed it) and nest the byline/subject inside `.content` (leaked into body); date fallback + strip `.author`/`h3.first` from the body; 11 forum docs ΣΔF1 +0.155, zero regression (rejected innermost-content which broke punbb −0.236)
- [0073 — raw-HTML dataset](0073-raw-html-dataset.md) — **+0.0048 F1, missing content solved**: full raw page (not pre-stripped fragment) recovers ~7 docs from F1≈0→1.0 (impulsegamer/nationalpost/etc were data-capture, not jusText bugs); small over-extraction losses are the new frontier; adopt datasets_rawhtml going forward
