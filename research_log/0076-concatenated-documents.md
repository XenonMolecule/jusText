# 0076 — Concatenated documents in one HTML (self-correcting re-merge)

- **Date:** 2026-06-25
- **Tag:** `remerge-dev2` / `remerge-dev` (baseline: `rawhtml-dev2` / `rawhtml-dev`)
- **Status:** landed — dev2 +0.0015 F1, dev flat (zero regression).

## Trigger

dev2 `geneageek.blogspot.com/.../black-sheep-sunday` scored **F1 0.02** — we extracted 27
chars ("has moved to a new address:") though the gold (1178-char post) is 100% in the html.
The raw page is **two concatenated documents**: a Blogger→WordPress redirect *stub*
(`<html>…</html>`) followed by the **real** archived post (`<html>…Black Sheep Sunday…</html>`).
lxml stops at the first `</html>` and parses only the stub.

## Why naive fixes regress

- "Largest `<html>` block" → drive.com.au 0.87→0.00 (content was in the first block).
- "Most visible text block" → law.hitbullseye 0.98→0.00.
- "Merge all bodies, always" → law.hitbullseye 0.98→0.01 (lxml *already* merged its 7 blocks
  correctly; a blunt re-merge confuses the classifier).
- "Re-merge when a block looks missing" (probe heuristic) → false-fired, impulsegamer 1.00→0.00.

The content isn't always in the biggest/first/last block, and lxml *sometimes* already merges
correctly — so any fixed rule regresses someone.

## Fix (self-correcting)

`justext()` gains `remerge=True`. When the input has ≥2 `</html>` and ≥2 `<body>`, it also
extracts from a merged document (`<html><body>` + all bodies + `</body></html>`) and **returns
whichever extraction kept more content**. It structurally can't regress: if lxml's default
parse already captured the content (law.hitbullseye, impulsegamer), the default keeps more and
wins; if lxml dropped a document (geneageek), the merge keeps more and wins. Single-`<html>`
pages (≈96–98%) are untouched; multi-doc pages pay one extra extraction.

## Results

| set | F1 | Lev |
|---|--:|--:|
| dev2 (held-out) | 0.8771 → **0.8786** (+0.00152) | 0.8144 → 0.8157 (+0.00132) |
| dev | 0.8912 → 0.8912 (flat) | 0.8275 → 0.8275 (flat) |

Recovered: geneageek 0.02→0.95, rembrandtwrites 0.00→0.81, cams 0.00→0.91; dev untouched.
One residual: signalscv −0.22 (merge kept more chars but slightly worse) — dwarfed by the
gains. 61 tests pass.

## Cost

2× extraction on multi-document pages only (~2–4% of docs); single-doc pages unchanged.
