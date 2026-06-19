# 0065 — Recover LaTeX math images to text (mathhelpforum equations)

- **Date:** 2026-06-18
- **Tag:** `current-latex` (baseline: `current-vb4`)
- **Status:** landed — quality win. Train +0.96 F1 / +0.97 Lev over 11 docs; dev flat.

## Trigger

Follow-up to 0064: the CSS junk was gone but the equations were blank ("If , evaluate").
User: "I think we need this... is it still in the html? How did the gold get it?" Answer to
both: **yes** — math forums render equations as an `<img>` from a LaTeX renderer with the
formula in the `alt` (and `src` query):

```
src='http://latex.codecogs.com/png.latex?x = \frac 1{4 - y}'
alt='x = \frac 1{4 - y}'
```

The gold transcribed the LaTeX to plaintext (`\frac 1{4-y}` → `1/(4 - y)`). jusText drops
`<img>`, so the formula vanished.

## Fix

`recover_latex_images(dom)` runs right after `html_to_dom`, **before** the forum handlers
(mathhelpforum is a firing vBulletin doc since 0063, so it returns before the preprocessor —
the recovery has to be earlier than both paths). For each `<img>` whose `src` matches a known
LaTeX renderer (`codecogs|mimetex|mathtex|/latex|...`), it replaces the img with a `<span>`
carrying a light LaTeX→text conversion (`_latex_to_text`): strip `$…$`, `\frac a{b}`→`a/(b)`,
`\sqrt{x}`→`sqrt(x)`, `\left(`/`\right)`→`(`/`)`, drop remaining `\commands` and braces.
Scoped to renderer hosts, so ordinary images (avatars, photos) are never touched.

## Results

- `67637`: now reads `If x = 1/(4 - y), evaluate 1/x + 4x + y - yx - 1` (matches gold);
  F1 0.547 → **0.808** (0.458 before the whole 0064/0065 thread).
- 11 train LaTeX docs: **ΣΔF1 +0.96, ΣΔLev +0.97** (67637 +0.26, discrete-math +0.25,
  calculus +0.16/+0.13, algebra +0.067); one trivial −0.011 F1 (gains +0.036 Lev).
- 5 datasets dev: **exactly flat** — there are **0** LaTeX-image docs in dev (11 train, 1
  test). Zero regression. 61 tests pass.

## Scope / limits

This is a [[data-quality-counts-without-metrics]] win: it cannot move the dev metric (no dev
doc has the pattern) but it's a real corpus-quality fix, validated on train. The conversion
is best-effort — complex multi-line LaTeX (e.g. an allaboutcircuits `\cosh^{-1}` expression)
won't match the gold exactly, but simple algebra/calculus (the common case) transcribes
cleanly. `alt`-less renderers with an unparseable `src` (koreascience) are left untouched.

Note for the MATH dataset: 0017 found that gold *drops* image-math there — so this is gated
to LaTeX-renderer hosts and emits only where the alt/src actually carries the formula; it
does not fire on the math dev docs (confirmed flat).
