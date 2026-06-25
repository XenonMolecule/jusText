# 0084 — Drop dangling UI-label paragraphs ("By" / "Share" / "Read More")

- **Date:** 2026-06-25
- **Tag:** `orphan-label-dev2` (baseline: `0083`)
- **Status:** landed — quality cleanup on 5 dev2 docs, dev2/dev flat (no regression).

## Trigger

User flagged slysa.org's "real disappointing weirdness": two bare **"By"** paragraphs plus a
**"Full Story"**. The "By" come from dead `sp-tweet` Twitter widgets — message, author link, and
timestamp are all JS-injected, so in the static snapshot only the template word "By" survives. A
scan found **7 dev2 docs** leaking a lone UI label: slysa (By, By, Full Story), theoutbound (Read
More, Share), plantengineering (Share), allaboutjazz (By), accesstoinsight (by), defenseone
(Author), wiki.call-cc (Author).

## Fix + the "Author" trap

`drop_orphan_ui_labels` marks as boilerplate any kept paragraph whose entire text is a UI control
or dangling byline prefix: `By|by|Share|Tweet|Like|Follow|Reply|Full Story|Read More|Posted by`.

**"Author" and "Comments" are deliberately excluded.** wiki.call-cc's gold *keeps* a standalone
"Author" (it's a real metadata field label there), while defenseone's "Author" is chrome — same
text, opposite desired treatment, no way to tell them apart by label alone. Excluding "Author"
keeps call-cc correct at the cost of leaving defenseone's one harmless extra label. "Comments" is
a kept thread marker (prior user guidance), so it's excluded too.

## Results

5 docs cleaned (slysa 0.869→0.873, plantengineering, allaboutjazz, accesstoinsight, theoutbound —
orphan labels gone); call-cc & defenseone keep their "Author" (no change). dev2 0.8803→0.8803,
dev 0.8913→0.8913 (both F1+Lev flat). 61 tests pass.

This is primarily a **quality** fix (removing embarrassing "By / By" output); the aggregate metric
barely moves since each drop is one short token.
