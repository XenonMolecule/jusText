# Research log

Chronological record of jusText experiments on the extraction benchmark. One file
per idea/version, newest insights captured while fresh. **Keep each entry under a
5-minute read.**

## Convention

- Files: `NNNN-short-slug.md` (zero-padded, monotonically increasing).
- Every entry names the jusText **run tag** it was measured with (`vX.Y.Z-<sha>`),
  so results trace back to cached runs under `benchmark/runs/<tag>/`.
- Compare against the previous version with `viz.py compare <prevTag> <thisTag>`.

## Iteration cycle

Each cycle is one pass of the loop below. A "cycle" maps to roughly one research log
entry and one commit — though a single hypothesis may take several un-committed edits
before it earns a commit.

1. **Backfill** — add the git commit id to the *previous* entry (now that it exists).
2. **Review** — skim prior entries; note anything to revisit or that informs today.
3. **Preregister** — write the hypothesis for this cycle *before* coding (a stub
   entry with Hypothesis filled in). Hypotheses are often engineering fixes.
4. **Revert (rare)** — if a past change should be undone, `git revert`/reset to the
   right commit first. Usually skipped.
5. **Change** — make the code changes to test the hypothesis.
6. **Measure** — run train/dev (`run_eval.py --tag <new>`); never test mid-cycle.
7. **Iterate** — refine and re-run freely. Multiple edits per hypothesis is fine and
   expected; not every edit is a commit.
8. **Log** — once the benchmark moves meaningfully (or the idea is ruled out), fill in
   the entry: Results (vs. prior tag via `viz.py compare`), Insights, Next.
9. **Commit** — commit the code + log entry together.
10. **Repeat.**

Guardrails: test split stays vaulted until milestones (`--allow-test`). Tune on
train/dev only. Domain splits are tiny — trust direction, not decimals.

## Entry template

```markdown
# NNNN — <title>

- **Date:** YYYY-MM-DD
- **Tag:** vX.Y.Z-<sha>   (baseline compared against: <prevTag>)
- **Status:** idea | in progress | landed | abandoned

## Hypothesis
One or two sentences: what we believe is wrong and what change should help.

## What changed
Bullet points of the actual code/heuristic change.

## Results
Small table vs. the comparison tag (dev/train; test only at milestones).
Net effect in one line.

## Insights
- What we learned (whether or not it worked). Failure modes confirmed/ruled out.

## Next
- Concrete follow-ups this surfaced.
```

## Index

general/dev F1: 0.762 (baseline) → 0.849 (0009) → 0.870 (0016 fastText) → **0.876** (0018 +dedup). Lev: 0.682 → **0.808**.
**Current best (ftstack+dedup):** general dev 0.876/0.808, train 0.877/0.811 | code 0.837 | science 0.982 | table 0.507 | math 0.806. Target 0.90/0.85.
table/dev: 0.0 → **0.449** (0009).

- [0001 — Baseline (jusText v3.0.2)](0001-baseline.md) — general 0.762/0.682
- [0002 — Relax good-anchor thresholds](0002-relax-good-anchor-thresholds.md) — **+0.047** (recall fix)
- [0003 — Learned RandomForest classifier](0003-learned-paragraph-classifier.md) — **+0.034** (opt-in model)
- [0004 — Labels (neg) + DOM features](0004-labels-and-dom-features.md) — +0.004; table +0.15
- [0005 — Threshold sweep (negative)](0005-threshold-and-plateau.md) — 0.5 optimal
- [0006 — Failure-taxonomy tool + ceiling](0006-failure-taxonomy-and-ceiling.md) — oracle 0.893
- [0007 — Content features (negative, reverted)](0007-code-math-content-features.md)
- [0008 — Code/math deep-dive](0008-code-math-deepdive.md) — text-stack +0.0035 (not shipped, runtime)
- [0009 — Stop fragmenting rows/lists](0009-row-list-segmentation.md) — **table +0.24**, raised oracle 0.893→0.902
- [0010 — Post-breakthrough sweep (negatives)](0010-post-breakthrough-sweep.md) — threshold/forms/language/separator not levers
- [0011–0013 — text-stack experiments](0013-fuzzy-text-stack.md) — fuzzy label (oracle 0.944), sklearn stack
- [0014–0015 — ceiling + failure deep-dive II](0015-failure-deepdive-2.md) — precision leak is context-dependent
- [0016 — fastText-on-100k stack](0016-fasttext-100k-stack.md) — general 0.870/0.801, +data breakthrough
- [0017 — math deep-dive](0017-math-deepdive-plan.md) — LaTeX-keep NEGATIVE; math-image detector; gold drops image-math
- [0018 — paragraph dedup](0018-dedup.md) — **BEST: general 0.876/0.808** (+0.006/+0.007, additive)
