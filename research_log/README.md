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

- [0001 — Baseline (jusText v3.0.2, unmodified)](0001-baseline.md)
