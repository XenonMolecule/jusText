# 0078 — dev2 under/over-extraction trend analysis (autonomous cycles)

- **Date:** 2026-06-25  **Set:** datasets_rawhtml general/dev2 (baseline jforum-dev2 F1 0.8792)
- **Status:** survey guiding the autonomous cycles; wins shipped separately (0076, 0077).

## Under-extracted docs (F1<0.7, ratio<0.7, content present): 13

| trend | docs | tractable? |
|---|---|---|
| JS-rendered SPA (pred≈0) | biography.com, cams.com | no — prune (0074/0075 detector routes them) |
| forum, gold KEEPS quotes | dhammawheel (`>`-quoted) | wall — gold-inconsistent (others drop quotes) |
| forum, body/post-count mismatch | guru3d, digit.in (gold "Post #21", page has 8 → pagination) | no — data mismatch |
| one-off directory (short detail dropped) | vegasmeansbusiness (keeps hotel names, drops addresses) | low value, one-off |
| wiki/specialized | ja.wiktionary, informatics.jax | one-off |

Net: the *clean* under-extraction levers (multi-doc 0076, JForum 0077) are shipped; the rest
are walls (quotes), data mismatches (pagination/SPA), or one-offs.

## Over-extracted docs (F1<0.75, ratio>1.5): 103 — the bigger frontier

Split into two populations:
- **Gold errors (tiny gold):** wikipedia Carry_On (gold 226), lifehacker (407), thenation (786),
  risingsun4x4club (180). These look like LLM gold truncation; matching them means *dropping
  real content* → forbidden by the data-quality rule ([[gold-underextracts]]).
- **Genuine over-extraction (chrome leak):** docwiki.cisco (2735 vs 27238), mozillazine faq.php,
  nvd.nist — full-page nav/sidebar/related leaking on raw HTML. Heterogeneous structures; a
  blanket content-drop risks regressing dev/train/test (the comment-removal study, 0068, showed
  this is net-negative).

## Conclusion

dev2's remaining frontier is dominated by walls, data mismatches, and gold errors. The two
clean, generalizable, non-regressing wins this session were structural: concatenated-document
re-merge (0076) and the JForum engine (0077). Over-extraction is large but contaminated by gold
errors; any blanket fix must be measured against dev/dev2/train/test for regressions before
shipping (user constraint).
