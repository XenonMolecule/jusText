# 0031 — Q&A role transform (StackExchange): role+author BEFORE body

- **Date:** 2026-06-17
- **Tag:** `0031-qa`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — biggest aggregate gain of the session.

## Idea (user — high priority)

For Q&A forums the gold applies a structural transform: it puts the **role + username
BEFORE** the post body (`**Question (forestclown)**\n<body>`, `**Answer (bmk)**\n<body>`),
in post order — so an assistant LLM preconditions on *who said what*. jusText instead dumps
the body then the username/score/tags *after*. This is **the** main transformation the gold
does on forum content; getting it right is high-value for downstream training data.

## Design

- **Detect**: StackExchange engine via DOM signature `div#question` (+ `div[id^=answer-]`).
  Reliable and engine-specific; the transform needs the structure anyway. (A fastText/URL
  classifier could generalise to other forum engines later, but the transform itself is
  SE-structure-specific, so DOM-signature gating is the clean call now.)
- **Transform**: emit `Title`, then per post `**Question|Answer (author)**` marker
  paragraph + the post body. Author = the post's `.owner`/`.user-details` link. Body is
  extracted by running `ParagraphMaker` on the `.post-text`/`itemprop=text` subtree, so it
  inherits the code-verbatim (0021), `<br>` (0025), list/separator (0009) handling. Comments
  are EXCLUDED (measured: including them lowers the match — the gold mostly omits them).
- **Integrate**: `justext(..., forum_qa=True)`; if SE detected, return the structured
  paragraphs (still run the 0023/0029 entity/FFFD passes on them).

## Results (prototype, 23 SE-family dev pages)

| | F1 | Lev |
|---|--:|--:|
| baseline | 0.7900 | 0.6924 |
| **SE transform (no comments)** | **0.8991 (+0.109)** | **0.8098 (+0.117)** |
| with comments | 0.8666 | 0.7560 |

Per-doc: superuser +0.22, mathematica +0.13, stackoverflow +0.12; english.SE −0.09 (its
gold includes comments — the exception). User accepts occasional dips for consistent gains.

## Full-set results (integrated, `justext(..., forum_qa=True)`)

| dataset/split | F1 | Lev |
|---|--:|--:|
| **general/dev (1000)** | 0.8832 → **0.8857 (+0.0025)** | 0.8175 → **0.8205 (+0.0030)** |
| code/dev | 0.8421 → 0.8418 (noise) | flat |
| math/dev (2) | 0.8214 → 0.8202 | 1 math.SE doc Lev 0.865→0.818 (holds F1 0.903) |
| science/dev | flat | flat |

**+0.0025 F1 / +0.0030 Lev on general/dev — the largest single-cycle gain this session**,
tied to the user's top-priority transformation. Integration uses synthetic marker
paragraphs + `ParagraphMaker` post bodies (so code/`<br>`/lists/entity/FFFD fixes all
apply). 61/61 tests pass. Detection = `div#question` DOM signature (engine-specific, robust).

## Next / refinements

- english.SE & math.SE dip slightly (their gold includes comments / different formatting) —
  a comment-inclusion heuristic could be doc-adaptive, but blanket comments hurt. Leave.
- Generalise to other Q&A engines (Discourse, phpBB) later — would need their DOM mapping.
