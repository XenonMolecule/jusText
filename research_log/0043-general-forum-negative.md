# 0043 — General forum detector (NEGATIVE, twice confirmed)

- **Date:** 2026-06-18
- **Status:** negative — not achievable with heuristics. Per-engine remains the path.

## Attempt

The audit (0042) showed 111/1000 dev forum docs, only 29 handled per-engine, 58 "other/
unknown". So I built a general detector: find >=3 username-anchored post blocks (links to
`/members//users//profile/` or class author/username/poster), scope each with `_post_container`
(0039), gate on the blocks covering >=40% of page text, body = the block's substantial
paragraphs minus the username/short lines.

## Result: fails on both axes

- **False fires**: fired on **52 NON-forum dev docs** (many pages have >=3 author/user links
  covering 40% of text — bylines, "related authors", widgets).
- **Garbage body**: even on the 8 real forum docs it caught, **mean ΔF1 −0.34** — without a
  per-engine body selector, taking "block paragraphs minus short lines" mixes in
  signatures/controls/nav and drops/duplicates content.
- 48/60 fired docs regressed >0.02.

This is the same wall as 0032. The per-engine handlers (SE/vBulletin/phpBB) work *because*
they anchor on a clean body element (`.post-text`, `#post_message_`, `.postbody`+`.content`);
a generic detector has neither reliable detection nor a clean body, and the gold is
unforgiving.

## Conclusion

**No clean general forum solution with heuristics** (user anticipated: "I don't know that we
will"). Reliable path = per-engine handlers, accepting they're incremental and skin-fragile:

- Shipped & correct: SE (0031), vBulletin (0039), phpBB (0040) — 29/111 forum docs.
- Per-engine to add (each needs its own body+author selectors + careful detection, validated
  on train-as-dev): XenForo (`.messageContent`, broke once), SMF (`.poster`+`.post`, +0.0233
  where it fired but detection misses skins), bbPress/WordPress (studiopress). Diminishing
  returns: more work per engine for fewer docs.

A learned router/classifier (fastText on big_train) could at least *detect* forum pages, but
the *transform* still needs per-engine structure, so detection alone doesn't close the gap.
