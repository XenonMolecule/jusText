# 0075 — Detector: route JS-rendered pages to a browser (`needs_javascript_render`)

- **Date:** 2026-06-25
- **Status:** landed — new API, validated on dev + held-out dev2.

## Idea (user)

We can't extract content trapped in JS state blobs (0074), but we *can* cheaply **detect**
those rare pages and route them to a headless browser that executes JS, then re-run jusText on
the rendered HTML. If it's ~0.3% of pages, the slow path is negligible.

## Detector

`justext.needs_javascript_render(html, paragraphs)` → bool. True only when a page is
**large** (≥20 KB), **script-heavy** (script text > 30% of the page), and jusText extracted
**almost nothing** (< 300 chars). Cheap — the script scan only runs once the content is known
to be tiny. (Pre-extraction `visible/html` ratio alone was too loose: 14/1000, false-flagged
script-heavy pages that extract fine like mashable 0.99 / food.com 0.98.)

## Validation

| set | flagged | precision (F1<0.6) | examples |
|---|--:|--:|---|
| dev (1000) | 3 (0.30%) | **3/3** | iheart 0.02, countryliving 0.15, webdeveloper 0.18 |
| **dev2 (1000, held-out)** | 2 (0.20%) | **2/2** | biography.com 0.00 (script-frac 0.83), travelandleisure 0.24 |

Generalises to the fresh set: 5 flagged across both, all genuine extraction failures on
data-driven SPAs, zero false positives.

## Usage

```python
paras = justext.justext(html, stop)
if justext.needs_javascript_render(html, paras):
    rendered = headless_browser_fetch(url)   # Playwright/Puppeteer/Selenium -- executes JS
    paras = justext.justext(rendered, stop)
```

Note: a non-JS text browser (lynx) won't help -- the content is never in the served markup; it
needs JS execution.

## Notes

- The content-length signal reflects *this* extraction, so it's model-aware (a tier that
  extracts more on a borderline page won't flag it -- correct behaviour).
- dev2 baseline (rawhtml, ftstack): F1 0.8771 / Lev 0.8144 -- the fresh hill-climbing set.
