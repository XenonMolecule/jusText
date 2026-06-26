# 0091 — Content-in-links rescue (override when the doc emits nothing)

- **Date:** 2026-06-25
- **Tag:** `rescue-dev3` (baseline: `0089`)
- **Status:** landed — hqnetwork 0.00→1.00, dev2 flat (0 fires), dev3 up. User's idea.

## Trigger

User: `hqnetwork.co.uk/equality-and-diversity` scored **F1 0.00**. Its whole content block (a course
catalogue: each course title + description) is wrapped in `<a>` tags, so every paragraph has
link-density ≈ 1.0 and the classifier kills all 41 as navigation.

## Why the broad version failed, and the gate that fixes it

Unwrapping long links *unconditionally* recovers hqnetwork but **regresses dev2 −0.005 to −0.006 at
every word threshold** — it re-admits related-article / link-directory / "read more" blocks the gold
drops (a net-negative recall lever, like the 0079 levers). The user's insight: only do it **when the
normal extraction emitted ~nothing**. A page that already extracted fine is never touched, so the
boilerplate-readmission that caused the dev2 regression can't happen.

## Fix

After the normal path (and remerge), if kept content < 300 chars, re-extract from a copy of the HTML
with paragraph-length (≥ 15-word) `<a>` links demoted to spans, and keep it if it recovers more
content (self-correcting, like remerge). `_unwrap_long_links` does the demotion.

## Results

dev3 prototype: fires on **2** docs — hqnetwork **0.00→1.00** and countryliving 0.19→0.21 — for
**dev2 +0.0000 (0 fires)**. The "emits nothing" gate is what makes the otherwise-negative lever a
clean win. dev3 0.8846→GUARDRAIL. 61 tests pass.

## Cost

One extra extraction pass only on near-empty (< 300 char) docs — a small fraction.
