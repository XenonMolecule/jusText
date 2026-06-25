# 0074 — Content trapped in `<script>` blobs (NEGATIVE: no general lever)

- **Date:** 2026-06-25
- **Dataset:** `datasets_rawhtml` general/dev
- **Status:** investigated — **negative**, no tractable general fix; prune/gold-ceiling.

## Trigger

On the raw-HTML dataset, `iheart.com/artist/Slayer-12754/...` still scores **F1 0.016** even
though the content is now "present" (gold-token coverage of the full html = 100%). User asked
whether JavaScript-trapped content is a general trend worth handling.

## Findings

- iheart's bio ("Slayer were one of the most distinctive…") lives inside a
  `<script type="text/javascript">BOOT={…big JSON…}</script>` app-state blob — jusText (and
  the preprocessor's `Cleaner`) correctly strips scripts, so it's removed. The gold's LLM read
  it out of the JS.
- **Prevalence:** of 986 dev docs, only ~2 are genuinely script-trapped *and* failing —
  iheart (F1 0.016) and countryliving (0.148). (memphis/infoplease "look" script-heavy but
  have visible copies too and score 0.97/0.83; theatlantic's 0.42 is a visible-content issue,
  only 15% in scripts.)
- **Not standardized.** iheart gold-in-JSON-LD = **4%** (its JSON-LD only has a short
  `description`); countryliving has **0** JSON-LD scripts. Each page uses a different bespoke
  JS structure.
- **JSON-LD `articleBody`** (the one safe, standardized hook): present in only **4** dev docs,
  and **0** of them are cases where we're failing — so extracting it helps nothing here.

## Verdict

No general lever. A generic "mine arbitrary JSON for content-like strings" extractor would
inject config/ad/metadata text across ~980 docs to rescue ~2 — clearly net-negative. These
are data-driven SPA pages that need JavaScript execution (headless render), outside jusText's
HTML-heuristic scope. Treat as **prune / gold-ceiling**, like the empty-page candidates. No
code change.
