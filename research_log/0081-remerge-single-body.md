# 0081 — Re-merge multi-document pages with a single matched `<body>`

- **Date:** 2026-06-25
- **Tag:** `remerge1body-dev2` (baseline: HEAD / `0080`)
- **Status:** landed — dev2 +0.0010 F1, dev flat (zero regression). Extends 0076.

## Trigger

dev2 `cams.com` scored **F1 0.00** (0 / 11547 chars). The raw page concatenates two documents:

- **Doc 1** — `<html>` … `</body>`@13603 … `</html>`@13611. A stub whose **opening `<body>` is
  malformed/absent**, so the `<body>…</body>` pair regex never matches it. Just nav chrome.
- **Doc 2** — `<body class="english gst">`@27037 … real content (Contact Us / billing) … `</body>`
  … `</html>`@64789.

lxml stops at doc-1's first `</html>` and never sees doc 2, so it extracted only the chrome
(domtext 7675; the gold content sits at offset 32286, past the cut).

## Why 0076 missed it

0076's `_merge_html_documents` required **≥2 `</html>` AND ≥2 matched `<body>` pairs**. cams has
2 `</html>` but only **1** matched body (doc 1's body never closed a pair), so the merge was
skipped. The ≥2-body guard was over-tight: the single matched body here *is* exactly the dropped
document.

## Fix

Relax the guard to **≥2 `</html>` and ≥1 `<body>`**. Everything else is unchanged: the caller
still extracts from both the default parse and the merged document and **returns whichever kept
more content**. Self-correction makes the relaxation safe — if the single body is one lxml
already parsed, the alt extraction matches the default and the default wins (no-op); if it's a
dropped document (cams), the alt recovers it and wins. The only cost is one extra extraction on
the handful of pages that newly qualify.

## Results

| set | F1 | Lev |
|---|--:|--:|
| dev2 (held-out) | 0.8792 → **0.8802** (+0.00099) | 0.8166 → 0.8174 (+0.00081) |
| dev | 0.8912 → 0.8912 (flat) | 0.8275 → 0.8275 (flat) |

cams.com 0.00 → **0.907**. 15 dev2 docs newly qualify for the merge; self-correction kept dev
perfectly flat and produced no dev2 regressions large enough to offset the cams gain. 61 tests
pass.

## Cost

One extra extraction on multi-`</html>` pages with ≥1 body (~1–2% of docs); single-doc pages
untouched.
