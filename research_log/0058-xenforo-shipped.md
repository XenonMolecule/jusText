# 0058 — XenForo handler SHIPPED (reverses 0057)

- **Date:** 2026-06-18
- **Tag:** `current-xenforo` (baseline: `current-068bdca` / 068bdca)
- **Status:** landed — forum role-transform, general +0.0002 F1 / +0.0004 Lev, 4 datasets flat.

## Trigger

User flagged `http://www.droidforums.net/threads/k9-mail-contacts.12435/` (dev general,
idx 844) as "completely broken / absolutely wrecked." It wasn't catastrophic by metric —
F1=0.934, Lev=0.868, *above* the 0.885/0.821 dataset mean — but the **rendered** output was
a wall of text: the 14 post bodies extracted fine (P=0.972) yet **every `**author (date):**`
marker was missing** (R=0.899; the ~480-char gap ≈ the 16 dropped markers), plus leaked
`Log in or Sign up`, XenForo post-number gutters (`10.`–`14.`), and trailing SEO tag spam.
The gold for this doc is the **canonical `**author (date time):**` format** — the exact
target the shipped SE/vB/phpBB/SMF/bbPress handlers already emit.

## What's different from 0057 (4th attempt, NEGATIVE)

0057 reported the XenForo handler net −0.02 F1 on the 69-train temp-dev and stopped. Re-run
with two changes flips it hard:

1. **Time recovery from the `.DateTime` `title` attr.** The visible text is only the day
   (`Dec 31, 2009`); the full stamp (`Dec 31, 2009 at 7:49 AM`) is in `title`. Pulling it
   and dropping ` at ` makes the marker match the gold's `(... 7:49 AM)`.
2. **Body element + assembler.** `blockquote.messageText` → `ParagraphMaker` captures the
   **full** body here (k9: 5460 vs gold 5674; the model gave 5190), unlike the under-extraction
   0057 blamed.

Measured (handler vs current shipped pipeline, per-doc):

| set | fired | ΣΔF1 | ΣΔLev |
|---|--:|--:|--:|
| general/dev | 6 | **+0.228** | +0.408 |
| general/train | 69 | **+0.741** | +1.111 (39 wins) |

k9 itself: F1 0.934 → **0.994**, Lev 0.868 → **0.959**.

## Quote policy (decided by sweep, not assumption)

XenForo gold **drops reply-quotes**. Keeping them craters train (−1.61 F1) — so quotes are
stripped (`_strip_quote_blocks`), same as the vB4-broadening revert. The one casualty is
`howtoforge/using-mod_spdy` (train, −0.37): its opening post pastes its own error logs
*inside a `quoteContainer`*, which the gold keeps. A per-post "keep quotes when stripping
guts the post" guard was swept (ratio 0.1–0.3) and **rejected** — the lost content isn't
concentrated in one quote, so every ratio that rescues howtoforge also keeps reply-quotes
elsewhere and nets negative. The two cases are structurally identical (`quoteContainer`, no
attribution) and can't be told apart cheaply. Plain strip (ratio 0.0) is the clear optimum;
the single train crater is dwarfed by 39 train wins and there is **no dev crater** (worst
dev doc −0.006, and it gains Lev).

## Ship gate (5 datasets dev, vs 068bdca)

- general F1 0.8852 → **0.8854** (+0.00023), Lev 0.8208 → **0.8212** (+0.00041)
- code / math / science / table: **exactly flat** (handler doesn't fire)
- 61 tests pass.

Canonical data-quality win ([[data-quality-counts-without-metrics]]): the metric barely
moves (token-based, marker tokens are a few % of the doc) but the thread now renders with
per-post attribution instead of an anonymous wall. Dispatched after bbPress in `justext()`.

## Next

- XenForo docs whose gold uses a *different* marker (physicsforums `[user] date`, brackets)
  still match on tokens, so F1 is unaffected; no action.
- howtoforge pasted-logs-in-quote remains the one known XenForo loss — gold-inconsistent,
  not cheaply gateable. Deferred.
