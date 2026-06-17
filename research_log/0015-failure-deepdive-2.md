# 0015 — Failure deep-dive II (fuzzy-label false-keeps/drops)

- **Date:** 2026-06-17
- **Tag:** (analysis on shipped model + cached dev features)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — insights to inform the 100k runs.

Used the **fuzzy label as ground truth** to categorize the shipped model's per-paragraph
errors on general/dev (no re-extraction — used cached features). Model keeps 30,062
paragraphs; 9,133 are **false-keeps** (teacher dropped) and 7,218 **false-drops**.

## What the model wrongly KEEPS (precision leak — the real headroom)

Semantic breakdown of the 9,133 false-keeps (median 13 words — substantial, not just nav):

| category | share of false-keeps |
|---|--:|
| **date/time tokens** | **24%** |
| byline ("By X", "wrote:") | 9% |
| comment/forum-meta | 6% |
| share/social, image-credit, legal, js-notice | 1–2% each |

Examples: `Shawn GuoSept. 9, 2013, 3:08 p.m.` · `05-14-2011, 08:18 AM` · `Jypster wrote:`
· `July 1980` · `You may not post attachments` · `Welcome to the CRG Discussion Forum!`

**The dominant leak is temporal/byline/forum-meta boilerplate (~33%).** But it is
**NOT rule-separable**: a blanket "drop lines that look like a date/byline" rule is only
**49% precise** — the teacher *keeps* many dates (article datelines, citation/pub dates
like `Published online Nov 11, 2009. doi:…`). Telling a forum timestamp (drop) from an
article dateline (keep) needs **text + context**, not a regex.

Other candidate rules ruled out: **encoding garbage** (mojibake `�…`) is only **0.2%** of
leaks — negligible.

## What the model wrongly DROPS (mostly not real)

7,218 false-drops, but **median 3 words, 74% ≤5 words** — these are short fragments the
fuzzy label spuriously marks "in gold" (their few tokens fuzzy-match somewhere). So the
"+0.03 MODEL_LIMITED headroom" is **largely illusory**; the real, reliable headroom is
**precision (false-keeps)**, not recall.

## Implications for the runs

1. **Favors the learned text model (fastText/100k) over bespoke rules** — the main leak
   is context-dependent boilerplate (forum vs article dates) that only a text+context
   model can separate. The 100k run is aimed at exactly this.
2. **Forum pages are a recurring hard sub-domain** (timestamps, "X wrote:", "You may not
   post…", "Welcome to the Forum"). Worth a per-category check once the 100k model lands.
3. **Evaluate on precision-leak reduction**, not recall — false-drops are label noise.
4. If adding features to the stack: a "temporal/byline-shape" feature may still help the
   *model* (as a soft signal it combines with context), even though a hard rule fails.
