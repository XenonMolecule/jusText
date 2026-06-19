# 0062 — Drop doubled list numbers (recipe steps)

- **Date:** 2026-06-18
- **Tag:** `current-dblnum` (baseline: `current-srcnl`)
- **Status:** landed — quality win, surgical (1 doc), zero regression.

## Trigger

User, same pillsbury recipe: "Are we able to avoid these double numbers things? Seems like a
simple thing to catch." The Directions rendered with doubled numbers:

```
ours               gold
1. 1 Heat oven     1. Heat oven
2. 2 In large bowl 2. In large bowl
```

## Cause

The step markup carries an **explicit source step number** plus the description:
`<li><span class="recipePartStepHeading">2</span><span>In large bowl...</span></li>`. Our
`<ol>` auto-marker injects `2. `, and the source `2` is content → `2. 2 In large bowl`. Step
1 was additionally orphaned (`1.` on its own paragraph, `1 Heat oven` on the next) because the
inner `<div>` broke the marker off.

## Fix

`fix_doubled_list_numbers` (post-classification, after `fix_orphaned_list_markers`):

- **within-paragraph** `^(N)\.\s+\1\b` → `N.` (drop the duplicate source number).
- **cross-paragraph** a bare `N.` paragraph followed by a kept paragraph starting with the
  same `N` → rejoin as `N. <text>` and drop the marker paragraph.

Gated on the doubling being **systematic** (≥2 items whose source number equals the marker
ordinal). A lone `1. 1 cup flour` is a real quantity and never triggers — the chance that ≥2
consecutive items' leading quantities coincide with their ordinals is nil.

## Results (5 datasets dev, vs current-srcnl)

- pillsbury: F1 0.9503 → **0.9564**, Lev 0.8527 → **0.8574**; Directions now read
  `1. Heat oven…`, `2. In large bowl…`.
- general F1 +0.000006 / Lev +0.000005; **exactly 1 doc changes**; other datasets flat.
- 61 tests pass.

## Next

- The same systematic signature would catch other CMSs that pre-number list items; none
  beyond pillsbury in this dataset.
