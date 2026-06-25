# 0077 — JForum forum role-transform (coderanch)

- **Date:** 2026-06-25  **Tag:** jforum-dev2 (baseline remerge-dev2)
- **Status:** landed — dev2 +0.0006 F1, dev flat.

## Trigger
dev2 `coderanch.com/t/346730` F1 0.376, content 100% present — JForum engine, no handler.

## Fix
`jforum_paragraphs`: authors in `.authorName(NoLink)`, bodies in `td.postbody` (separate rows
of one table), paired by document order; date from `.postdetails`. Gated on >=2 posts with
authors==bodies. Dispatched after workitmom.

## Results (rawhtml)
- coderanch/346730 (dev2) 0.376→0.970; train 0.540→0.976, 0.924→1.000, 0.871→0.966.
- dev2 F1 +0.000594 / Lev +0.000785; dev −0.000014 (one doc 354104 0.969→0.955, marker-format
  noise; dev aggregate noise); 61 tests pass. 6 coderanch docs fire, 5 win.
