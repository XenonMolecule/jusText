# 0032 — Forum generalization beyond StackExchange (exploration)

- **Date:** 2026-06-17
- **Status:** exploration — landscape mapped, general-extractor ruled out, per-engine path chosen.

## Goal (user)

Generalize the 0031 Q&A role-transform beyond StackExchange. Build an eval subset by
grepping the gold for forum markers; explore a general detector (fastText on big-train) and
non-bespoke handling. "So much possibility to fix forums and comments beyond the SE fix."

## Eval subset (gold-marker grep)

Markers: `**Question/**Answer` (Q&A) and `**user** (post #N)` / `**user** (date)` (threads).

| family | dev docs | current F1 | current Lev |
|---|--:|--:|--:|
| Q&A — StackExchange | 19 | 0.891 | 0.814 |
| Q&A — non-SE (justanswer, medhelp, moz, realself…) | 5 | 0.893 | 0.814 |
| forum threads (phpBB/vBulletin/…) | 20 | **0.890** | **0.781** |

Key insight: forum threads are **already F1-good (0.89)** — the opportunity is **Lev /
role-before-body formatting** (and the user's LLM-precondition goal), not content recall.

## General extractor: RULED OUT

Prototyped a single heuristic forum extractor (union of common body/author selectors:
`postbody`/`post_message`/`postcontent`/`message`, `author`/`username`). On the 20 dev
threads it **fired on only 1 and regressed −0.018 F1 / −0.016 Lev**. Engines differ too much
(even vBulletin versions split between `#post_message_N` and `.message`) for one rule.
Per-engine handlers (like SE) are the viable path.

## Engine breakdown (forum/QA docs)

train(362): other/unknown 126, **StackExchange 100 (done)**, **vBulletin 75**, phpBB 39,
XenForo 14, SMF 6. dev(44): SE 19, vBulletin 11, other 9, phpBB 2, SMF 2, XenForo 1.

## Plan

1. ✅ StackExchange (0031).
2. **vBulletin handler** — biggest remaining engine (75 train / 11 dev). Same shape as SE:
   detect (vBulletin signature), per-post `**username** (date)` + body via ParagraphMaker.
3. phpBB handler (39 / 2).
4. fastText forum **detector** from big_train (982 MB available) — only useful as a *router*
   to handlers; build once ≥2 handlers exist, to catch the unknown/long-tail.

## Notes

- Comments: blanket-excluding hurt some docs (english.SE); the gold is inconsistent. Worth a
  doc-adaptive comment policy later (user flagged the gold may not be most correct here).
- Non-SE Q&A (5 dev) already ~0.89 — low marginal value; fold into a general Q&A handler later.
