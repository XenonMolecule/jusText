# 0027 — Escape angle-bracket emails (forum/usenet quoting)

- **Date:** 2026-06-17
- **Tag:** `0027-email`
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — large per-doc win on forum pages, zero regression.

## Idea

User: forum pages "get butchered by weirdness with the indents" (fixunix.com VXVM thread).
Diagnosed: Usenet-style quoting writes `"Joe" <joe.poulos@cendantmobility.com> wrote:`.
**libxml2 parses `<joe.poulos@cendantmobility.com>` as a bogus tag and drops it** —
losing the address *and* mashing the surrounding text (`lxml.text_content('"Joe" <a@b>
wrote')` → `'"Joe"  wrote'`). The gold keeps the 10 emails on that page.

Fix: before parsing, escape `<addr@host>` to `&lt;addr@host&gt;` so it stays as text.
Pattern `<([a-zA-Z][^<>\s]*@[^<>\s]*)>` — the `@` before any space means it can't be a real
tag (real tags have a space before attributes), so it never touches `<a href="mailto:x@y">`.
Under the `fix_encoding` flag, alongside mojibake/entity repair.

## Results (ftstack model)

| | F1 | Lev |
|---|--:|--:|
| **fixunix VXVM (idx 402)** | 0.740 → **0.960** | 0.574 → **0.921** |
| fixunix kernel (idx 120) | 0.576 → **0.629** | 0.436 → 0.455 |
| general/dev (1000) | 0.8825 → **0.8827** | 0.8165 → **0.8169** |
| code/math/science/table | flat | flat |

Only **2/1000** dev docs have the pattern (tiny aggregate) but a **+0.22 F1** swing where it
applies. All matches verified real emails (`mroos@linux.ee`, …) — no false hits on tags.
61/61 unit tests pass.

## Next

- Forum post-author markers (gold: `**unix** (post #N):`) — we capture "Thread:/Re:"
  instead. Harder (post-structure parsing); deferred.
- Deferred queue: fixunix done; weatherbase broken symbols (next); contentdm spacing.
