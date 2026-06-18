# 0028 (PLANNED) — Forum "Quote From" / reply-quote handling

- **Status:** planned, but DEPRIORITIZED — user checked the shared example and jusText
  actually handles it **better than the gold** (2026-06-17). The premise ("gold is
  smarter about reply-quotes") does not hold for this page. Keep as a general watch-item,
  not an urgent fix.
- **Example:** http://forum.linuxmce.org/index.php?topic=8879.msg60617 (jusText > gold here)

## Problem

Forum reply features quote the parent post ("Quote from: X on …"). jusText keeps **every
copy**, so the same text appears many times (the original post + each reply that quotes it)
→ lots of **repeated tokens**. The gold extractor is smarter: it understands the reply/quote
structure and doesn't duplicate. Related to the dedup pass (0018) but more structural —
quoted blocks are *near*-duplicates with a "Quote from:" header, often nested.

## Directions to think about

- Detect forum quote blocks (`<blockquote class="...quote">`, "Quote from: … on …",
  bbcode quote markers) and handle them deliberately — drop or collapse repeated quotes,
  or attribute them once.
- Be careful: quoting is legitimate context sometimes (the gold *does* keep some quotes,
  e.g. the usenet `>`-quoted text in fixunix 0027). Goal is to match the gold's smarter
  behaviour, not blanket-drop quotes.
- Measure against the dedup pass (0018) — is this just stronger dedup, or a new quote-aware
  rule? Check repeated-token rate before/after on forum pages.

## Note

This is the "be careful about repeated tokens" theme the user flagged. Tie to the forum
work in 0027 (angle-emails) — both are forum-formatting quality.
