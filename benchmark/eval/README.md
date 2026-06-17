# jusText benchmark eval + analysis tools

Measure a jusText build against the LLM-distilled gold (`final_output`) and analyze
where it goes wrong. **Train/dev only** — the test split is held out; the loaders
refuse it until the final run.

## Layout

| file | role |
|------|------|
| `run_eval.py` | run jusText over a split → cache predictions + per-doc metrics + summary |
| `metrics.py`  | ROUGE-L (LCS F1) + char-level Levenshtein, both via `rapidfuzz` |
| `analysis.py` | importable `Doc`/`Run` model: ranking, search, breakdowns, diff, version compare |
| `viz.py`      | text-only CLI on top of `analysis.py` |

Outputs live in `benchmark/runs/<tag>/<split>.{predictions,metrics}.jsonl` + `summary.json`.
`<tag>` defaults to `v<version>-<gitsha>` (`-dirty` if uncommitted), so every jusText
build is cached separately and stays comparable.

## Typical loop

```bash
# 1. evaluate the current build (auto-tag from git)
python benchmark/eval/run_eval.py --split dev

# 2. see where we stand
python benchmark/eval/viz.py overview            # distribution, failure tags, breakdowns
python benchmark/eval/viz.py rank --worst --n 20 # worst docs (add --flag has_code)
python benchmark/eval/viz.py tags                # failure-mode taxonomy w/ examples

# 3. hunt patterns
python benchmark/eval/viz.py search --dropped 'def |class |import ' --flag has_code
python benchmark/eval/viz.py diff <id> --only dropped   # what jusText threw away

# 4. ... change jusText, re-run with a new --tag, then compare versions
python benchmark/eval/run_eval.py --split dev --tag fix-code-blocks
python benchmark/eval/viz.py compare v3.0.2-9fb3340 fix-code-blocks
python benchmark/eval/viz.py runs                # list everything cached
```

`compare A B` joins per-doc by id and reports the mean delta plus the biggest
regressions / improvements — so we can see the exact effect of each change.

## Importable API (for ad-hoc analysis)

```python
from analysis import load_run, compare
run = load_run("v3.0.2-9fb3340", "dev")   # tag=None -> latest run
run.worst(10); run.best(10); run.around_median(10)
run.find(diff_dropped=r"def |class ", has_code=True)   # regex over dropped spans
run.breakdown("has_code"); run.tag_counts(); run.percentiles()
d = run.get("025fbdd9")                    # by id or unique prefix
list(d.diff_ops("word"))                   # ('delete'|'insert'|'equal'|'replace', gold, pred)
```

## Failure tags (heuristic, primary = highest priority)

`ERROR` · `EMPTY_PRED` (returned nothing) · `NON_LATIN` (stoplist-language mismatch) ·
`UNDER_EXTRACT` / `OVER_EXTRACT` (length ratio <0.5 / >1.5) · `WHITESPACE` (only
whitespace differs) · `PARTIAL` · `GOOD` (F1 ≥ 0.95).
