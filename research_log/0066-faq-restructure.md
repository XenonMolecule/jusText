# 0066 — Restructure semantic FAQ accordions (oshidefender)

- **Date:** 2026-06-18
- **Tag:** `current-faq` (baseline: `current-latex`)
- **Status:** landed — quality win, surgical (1 doc), zero regression.

## Trigger

User: the FAQ section of `oshidefender.com/.../troj-fakeav-bls` "gets messed up badly." Gold
is a clean `Frequently Asked Questions` header + `question\nanswer` pairs; our output had the
questions detached from their answers, plus template chrome.

## Cause

Off-canvas/accordion FAQ: the questions appear **twice** — once in a `<ul class="questions">`
trigger list (first in document order), once in `div.faq` blocks holding the real
`div.question` + `div.answer`. The model's dedup keeps the trigger copy and **drops the
answer-block question**, orphaning every Q from its A. The `Frequently Asked Questions` header
(`<h4>`) was also dropped, and per-block chrome (a `Question` label, a vote `<form>`/`0%`)
leaked.

## Fix

`restructure_faq(dom)` (run after `html_to_dom`, before the handlers), **gated on >=2 real
`div.faq` question+answer blocks** so non-FAQ pages are untouched:

1. Drop the duplicate `ul.questions` trigger list -> dedup no longer orphans the questions.
2. Within each `div.faq`, strip template chrome (`<label>`, vote `<form>`, `.vote`/`.helpful`).
3. Drop the trigger `div.faq` that has no real answer.

Everything is scoped to the FAQ blocks — no global comment/vote removal (which the WordPress
comment study showed is net-negative). A residual `0 comments` from a separate `div.comments`
widget is left rather than risk a broad comment strip (2 tokens).

## Results (5 datasets dev, vs current-latex)

- oshidefender: F1 0.9117 -> **0.9739**, Lev 0.8632 -> **0.9525**; FAQ now renders as the
  gold's header + paired Q/A.
- general F1 +0.000062 / Lev +0.000089; **exactly 1 doc changes**; other datasets flat.
- 61 tests pass.

## Insight

A duplicated-content template (trigger list + real blocks) turns dedup against us: it keeps
the *navigational* copy and drops the *content-adjacent* copy. Removing the duplicate at the
source — rather than fighting the dedup — restores the pairing. The same shape (`div.faq` +
`.question`/`.answer`) generalizes to other accordion FAQs in the wider corpus, while the
>=2-block gate keeps it inert everywhere else here.
