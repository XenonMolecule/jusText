# 0038 — vBulletin role-transform attempt 2 (reverted: misattribution)

- **Date:** 2026-06-18
- **Status:** reverted — username misattribution across skins. Not shipped.

## Context

User chose "ship as data policy" (accept ~0.001 F1 dip) after I confirmed the gold brings
the username to the front on **every** forum thread (traxxas/fitness/straightbourbon/codeguru
all reorder). Built a vBulletin handler mirroring SE: `#post_message_N` bodies →
`**username** (date)` + body, with embedded "Originally Posted by..." quote blocks stripped
(fixed the over-inclusion; the metric went from −0.016 to flat).

## Why reverted (a correctness bug, not format-noise)

The per-post **username scoping is unreliable across vBulletin skins**:
- Loose container walk → when a post's body isn't under an `id="post_<n>"` ancestor (common
  on non-codeguru skins), the walk overshoots and grabs the **page's first** username, so
  every post is mis-attributed (thefiringline: SDC's post labelled `**helike1**`). Wrong
  author attribution would **poison** the training corpus — the exact opposite of the goal.
- Strict container walk (require an `id="post_<n>"` ancestor) → fires on **0** dev docs;
  these skins don't nest the body that way.

Date extraction also failed on several skins (empty parens). vBulletin's per-skin DOM
variation defeats a single scoping rule. Shipping wrong usernames is worse than not shipping,
so the handler was reverted (core.py back to 0037; SE handler intact, 61 tests pass).

## What would be needed

Robust per-post scoping that works across skins — pair each `post_message_N` body with the
username/date in *its own* post header by structural proximity (nearest-common-ancestor that
isn't shared with another body), validated per skin. Or the fastText router to gate + a small
set of per-skin handlers. This is real work; deferred rather than ship corpus-poisoning data.

## Standing win

The StackExchange handler (0031, +0.109 F1 on SE) remains the solid, correct forum transform.
The user's insight (gold transforms all threads) is validated and worth revisiting with a
correctness-first scoping approach.
