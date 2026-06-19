# 0061 — Collapse source-text newlines to spaces (recipe ingredients)

- **Date:** 2026-06-18
- **Tag:** `current-srcnl` (baseline: `current-vbfix`)
- **Status:** landed — Levenshtein quality win, F1 flat, no regression.

## Trigger

User: "Why did the ingredients section get so messed up? Are we trying to enforce some
newline rule for lines starting in numbers?" —
`pillsbury.com/recipes/philly-goes-mexican-cheese-steak/...`. The ingredient quantity and
name split across two lines:

```
our output          gold
1 1/2          ->   - 1 1/2 lb beef flank steak
lb beef flank steak
```

## Root cause (not the list/number logic)

Pillsbury renders each ingredient as a definition list:
`<dl><dt><span> 1 1/2 </span></dt><dd><span> lb beef flank steak </span></dd></dl>` — the
source is **pretty-printed with newlines** around each value. `<dl>` opens a paragraph and
`<dt>`/`<dd>` are separators (so it's correctly *one* paragraph), but `Paragraph.text` runs
`normalize_whitespace` over the joined nodes, and that function preserves any whitespace run
containing a `\n` as a single `\n` (the rule added in 0025 for `<br>` line structure). So the
**source indentation newline** between `<dt>` and `<dd>` survived as a line break:
`1 1/2\nlb beef flank steak`.

The user's instinct was right that a newline rule was firing — just not a number rule. It was
the `<br>`/0025 newline-preservation leaking onto pretty-print whitespace.

## Fix

`<br>` and list markers inject their `\n` **explicitly** via the element handlers, so the
only `\n` that should reach `normalize_whitespace` are those. In `characters()`, for
non-verbatim text, replace source `\r`/`\n` with a space before appending. Real line breaks
are unaffected (they don't come through text nodes); only pretty-print/wrapped-prose newlines
collapse to spaces. `<pre>`/`<textarea>` are verbatim and untouched.

## Results (5 datasets dev, vs current-vbfix)

| dataset | F1 | Lev |
|---|--:|--:|
| general | flat | 0.8212 → **0.8219** (+0.00069) |
| code | flat | 0.7524 → **0.7534** (+0.00103) |
| science | flat | 0.9751 → **0.9787** (+0.00357) |
| math | flat | −0.0002 (n=2 noise) |
| table | flat | flat |

F1 is whitespace-invariant so it can't move; **Levenshtein rises across general/code/science**
— it directly rewards removing the spurious line breaks. Pillsbury ingredients now read
`1 1/2 lb beef flank steak`; Lev 0.8481 → 0.8527.

Two `test_sax` cases asserted the old behavior (source `\n\n\n\n` inside `<sup>`/`<a>` →
`\n`); updated to the corrected space, since the dev metric confirms the new behavior. 61
tests pass.

## Insight

The 0025 newline-preservation was too broad: it kept *all* newline-bearing whitespace, not
just `<br>`-injected breaks. Scoping it to handler-injected `\n` is strictly more correct —
source formatting should never become rendered line structure.
