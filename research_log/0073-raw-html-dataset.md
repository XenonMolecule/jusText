# 0073 — Raw-HTML dataset recovers missing content (net +0.0048 F1)

- **Date:** 2026-06-25
- **Dataset:** `benchmark/datasets_rawhtml/` (same 1000 dev docs/urls/gold as
  `benchmark/datasets/`, but the `html` field is the **full raw page** instead of a
  pre-stripped fragment).
- **Status:** measured — raw HTML is net-positive and more realistic; adopt it as the
  benchmark going forward.

## Why

Earlier analysis (WARC-decoding doc) found the stored `html` was a *pre-stripped fragment*:
only 9/1000 dev docs were full pages, and ~12 had the gold body **absent** from the html
(F1≈0). Those weren't jusText bugs — the content wasn't there. The raw-HTML dataset restores
the full page.

Spot check (gold tokens present in html): iheart/Slayer 9% → **100%**; webdeveloper 45% →
**99%**.

## Result (general dev, ftstack model)

| dataset | F1 |
|---|--:|
| current (pre-stripped) | 0.8864 |
| **raw HTML** | **0.8912** (+0.00479) |

- **Gains** (recovered content, F1≈0 → ≈1.0): impulsegamer, jewishworldreview, law.miami,
  memphis, nationalpost (the "empty page" prune candidates), theatlantic. The missing-content
  problem is *solved* by feeding the full page.
- **Losses** (raw page is harder — more nav/script/related chrome leaks): anddev −0.144,
  ruby5 −0.118, ancestry −0.055, torah −0.053, … (8 docs > 0.02). These are the **new
  frontier**: genuine over-extraction that better boilerplate filtering should fix.

## Takeaways

- The pre-stripped dataset was "easy mode" that masked **data-capture** failures as
  **extraction** failures (iheart, webdeveloper were never jusText bugs).
- Raw HTML is what production actually feeds jusText (cf. the WARC-decoding guidance: feed the
  whole page), so it's both more realistic and higher-scoring.
- Next cycles should run against `datasets_rawhtml` and target the over-extraction losses.

## Note

The raw-HTML `*.jsonl.gz` files are large and left untracked (not committed); they live under
`benchmark/datasets_rawhtml/` locally.
