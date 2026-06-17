# 0008 — Code/math deep-dive + text-content model

- **Date:** 2026-06-17
- **Tag:** (analysis, vs `0004-dom-features`)
- **Commit:** _(backfilled next cycle)_
- **Status:** landed — marginal/negative; plateau holds. Nothing shipped.

## What we tried (per user: target code/math; bespoke rules OK; richer content features)

**1. Why code fails (inspection).** On the `code` set, jusText classifies code blocks
**erratically** — `/// <summary>` kept (`good`) while `/** <summary>` and
`namespace X;` dropped (`bad`/`short`). Code has low stopword density so it bounces
between classes. Critically the code sits in `<div>`s (syntax highlighting), **not
`<pre>`/`<code>`**, so DOM tags can't catch it.

**2. Bespoke code force-keep rule** (keep paragraphs that look like code: high
symbol density or code keywords + `;{()`):

| dataset | base F1 | +code-rule |
|---|--:|--:|
| code | 0.814 | 0.820 (+0.006) |
| general | 0.847 | **0.840 (−0.007)** |
| math | 0.811 | **0.784 (−0.027)** |
| science | 0.970 | **0.929 (−0.041)** |

Helps code a little, **hurts everything else** (110k spurious keeps on general — it
catches symbol-heavy non-code). Fails the domain-agnostic test. **Rejected.**

**3. Text-content model** (char 3–5gram HashingVectorizer + SGD logistic on paragraph
text): standalone F1 0.795 (weaker than structural). **Stacked** as a feature into the
RF: general dev 0.847→**0.850** (+0.0035), Lev →0.774 — the only positive, but
**+8 ms/doc** (≈2× inference). Given runtime is a hard objective, not worth +0.0035.
**Not shipped.**

## Insights

- Code failure is a **segmentation/classification** issue, not a feature gap — and the
  natural fixes (symbol rules) aren't domain-agnostic-safe: what reads as "code" on a
  code page reads as boilerplate JS/markup on a general page.
- The plateau (~0.847 general) is now confirmed across **8 cycles / ~10 levers**. The
  only positive lever (text-model stack) costs 2× runtime for +0.0035.

## Conclusion / recommendation

`0.847 F1 / 0.770 Lev` (from 0.762/0.682 baseline) is the **practical ceiling** of fast,
CPU-only paragraph selection on this LLM-distilled gold. The 0.6-oracle is 0.893 and the
residual gap is diffuse + partly gold-noise. **0.90/0.85 needs a different paradigm**
(semantic/generative extraction like the teacher) that conflicts with the ms/doc budget.
Recommend: ship the `0004` learned model as the result; revisit only if the runtime
budget is relaxed or the gold is cleaned.

## Next

- Hold for user direction (relax runtime? clean gold? accept ceiling?). Meanwhile:
  consolidate — wire the learned model as a documented, easy-to-use config.
