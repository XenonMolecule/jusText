# 0057 — XenForo handler, 4th attempt (NEGATIVE, not shipped)

- **Date:** 2026-06-18
- **Tag:** (validation only; nothing wired into core.py — repo stays at 5a82a1b)
- **Status:** abandoned — net-negative on the 69-doc train temp-dev; gold-inconsistency wall.

## What changed vs prior attempts

Prior attempts (queue) fired on only **2/71** train docs — container detection was wrong.
This time the container is correct:
`//*[contains(concat(" ",@class," ")," message ") and @data-author]` — the post block, with
the author in `data-author`, body in `blockquote.messageText`, date in `.DateTime`. It now
**fires on 69 train docs** (validated as a temp dev, the method that caught the breakage).

## Results (xenforo_paragraphs vs baseline, 69 train docs)

| variant | F1 | Lev |
|---|--:|--:|
| baseline (no handler) | **0.857** | **0.767** |
| strip quotes | 0.831 (−0.026) | 0.732 |
| keep quotes + `**user** (date)` | 0.837 (−0.020) | 0.739 |

Net-negative either way; worst docs −0.5 (howtoforge new=927 vs gold=3593).

## Why it fails (the walls)

1. **Severe body under-extraction.** Gold is 3–4× larger than the extracted post bodies on
   the worst docs — and it's NOT mainly quotes (keeping quotes recovered only +0.006). The
   `blockquote.messageText` doesn't capture the full gold content; gold also keeps the
   thread subtitle ("Discussion in '…' started by …, <date>") and more.
2. **Gold marker format is inconsistent across XenForo docs:** talkbass gold uses
   `**subdude67** (Nov 20, 2012 6:19 AM)`, physicsforums gold uses `[tmclary] Jun 23, 2008
   09:26 AM` (brackets). No single marker format matches. (Doesn't affect F1 — tokens are the
   same — but confirms the gold has no consistent XenForo transform to target.)

## Verdict

Container detection is solved, but the body element isn't clean/complete and the gold is
inconsistent — the same "per-engine handlers only win with a CLEAN body element" wall
(queue / 0046) plus the quote gold-inconsistency that killed vB4 broadening. 4th XenForo
attempt, 4th negative. **Stop pursuing XenForo** unless the body-completeness problem is
cracked. Not wired into core.py (it would regress general/forum docs).
