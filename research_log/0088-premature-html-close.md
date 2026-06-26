# 0088 — Premature `</html>` close (content after an empty body)

- **Date:** 2026-06-25
- **Tag:** `premclose-dev3` (baseline: `0087`)
- **Status:** landed — thursdayreview 0.00→0.99, dev2/dev/dev3 flat-to-up (self-correcting).

## Trigger

dev3 `thursdayreview.com/WhiteHouseCyberAttack.html` scored **F1 0.00** (we extracted nothing).
Its HTML is malformed:
```
<html><head></head><body></body></html>      <- empty, closes immediately
<title>Russians May Have Been Behind ...</title>
<meta ...> ... <article body> ...             <- ALL content is AFTER </html>
```
lxml stops at the premature `</html>` and parses the empty body → `domtext = 1`. The whole article
sits *after* `</html>` as loose markup, with no second `<html>` wrapper — so the 0076/0081 remerge
(which needs ≥ 2 `</html>`) doesn't catch it.

## Fix

Extend `_merge_html_documents` (the self-correcting remerge family) with a second case: if a
`</body></html>` is immediately followed by more markup (`</body>\s*</html>\s*(?=<)`), drop that one
premature close so lxml keeps the trailing content. The caller already re-extracts from the result
and **keeps whichever yields more content**, so this can't regress a page lxml parsed correctly (a
legitimate trailing close has nothing after it, so the regex never matches; a spurious match that
adds no content loses the size comparison).

## Results

thursdayreview 0.00 → **0.993**. cams.com (0081 concatenated-doc case) still 0.907 — both
malformations now flow through one self-correcting path. dev3 0.8837→0.8841 (+0.0004 F1, +0.0005 Lev), dev2 0.8804 flat, dev 0.8913 flat. 61 tests pass.

## Scope

Genuine "content after a premature `</html>`" is rare (thursdayreview is the clear dev3 case;
artedguru's trailing content is scripts, not the article, so it stays 0.70). A clean structural
bug fix, not a big cluster.
