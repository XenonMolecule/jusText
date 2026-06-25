#!/usr/bin/env python3
"""Run a local jusText build over a benchmark split and score it.

Two stages, written to ``benchmark/runs/<tag>/``:

    1. run    -> <split>.predictions.jsonl   (jusText output per doc + timing)
    2. score  -> <split>.metrics.jsonl       (ROUGE-L + Levenshtein per doc)
                 <split>.summary.json        (aggregate scores, timing, config)

``<tag>`` identifies the jusText version/config being evaluated; it defaults to
``v<version>-<git-sha>`` so different jusText builds land in separate folders and
stay comparable. Use ``--skip-run`` to re-score existing predictions without
re-running jusText.

Examples
--------
    python benchmark/eval/run_eval.py --split dev
    python benchmark/eval/run_eval.py --split dev --tag my-experiment --workers 8
    python benchmark/eval/run_eval.py --split dev --skip-run        # re-score only
    python benchmark/eval/run_eval.py --split dev --limit 50        # quick smoke test
"""

import argparse
import gzip
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from statistics import mean, median
from time import perf_counter

# Make both the repo root (for `justext`) and this dir (for `metrics`) importable,
# regardless of where the script is invoked from.
_HERE = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(BENCH_DIR))

import justext  # noqa: E402
from metrics import score_pair  # noqa: E402

DATASETS_DIR = os.environ.get("JUSTEXT_DATASETS_DIR", os.path.join(BENCH_DIR, "datasets"))
DEFAULT_DATASET = "general"
PARAGRAPH_SEPARATOR = "\n\n"

# --------------------------------------------------------------------------- #
# jusText worker (runs in a process pool; stoplist built once per worker)
# --------------------------------------------------------------------------- #
_STOPLIST = None
_MODEL = None


def _init_worker(language, model_path):
    global _STOPLIST, _MODEL
    _STOPLIST = justext.get_stoplist(language)
    if model_path:
        from justext.classifier import ParagraphClassifier
        _MODEL = ParagraphClassifier.load(model_path)


def _extract(item):
    """Run jusText on one doc. Returns a prediction record (no gold)."""
    index, html = item
    start = perf_counter()
    try:
        paragraphs = justext.justext(html, _STOPLIST, model=_MODEL)
        kept = [p for p in paragraphs if not p.is_boilerplate]
        prediction = PARAGRAPH_SEPARATOR.join(p.text for p in kept)
        error = None
    except Exception as exc:  # one bad doc must not kill the run
        paragraphs, kept, prediction, error = [], [], "", repr(exc)
    return {
        "index": index,
        "prediction": prediction,
        "n_paragraphs": len(paragraphs),
        "n_kept": len(kept),
        "runtime_ms": (perf_counter() - start) * 1000.0,
        "error": error,
    }


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def load_split(dataset, split):
    path = os.path.join(DATASETS_DIR, dataset, f"{split}.jsonl.gz")
    if not os.path.exists(path):
        available = (sorted(os.listdir(DATASETS_DIR))
                     if os.path.isdir(DATASETS_DIR) else [])
        sys.exit(f"Split not found: {path}\nAvailable datasets: {available}")
    records = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def default_tag():
    version = getattr(justext, "__version__", "unknown")
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=BENCH_DIR,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        dirty = subprocess.call(
            ["git", "diff", "--quiet"], cwd=BENCH_DIR,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return f"v{version}-{sha}{'-dirty' if dirty else ''}"
    except Exception:
        return f"v{version}"


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize(values):
    if not values:
        return {"mean": None, "median": None, "min": None, "max": None}
    return {
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
        "max": max(values),
    }


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #
def run_stage(records, language, workers, model_path=None):
    htmls = [(i, r.get("html", "")) for i, r in enumerate(records)]
    start = perf_counter()
    if workers == 1:
        _init_worker(language, model_path)
        results = [_extract(item) for item in htmls]
    else:
        with ProcessPoolExecutor(
            max_workers=workers, initializer=_init_worker, initargs=(language, model_path)
        ) as pool:
            results = list(pool.map(_extract, htmls, chunksize=16))
    elapsed = perf_counter() - start

    results.sort(key=lambda r: r["index"])
    predictions = []
    for record, result in zip(records, results):
        predictions.append({
            "warc_record_id": record.get("warc_record_id"),
            "url": record.get("url"),
            "snapshot": record.get("snapshot"),
            "prediction": result["prediction"],
            "n_paragraphs": result["n_paragraphs"],
            "n_kept": result["n_kept"],
            "runtime_ms": result["runtime_ms"],
            "error": result["error"],
        })
    return predictions, elapsed


def score_stage(records, predictions):
    start = perf_counter()
    rows = []
    for record, pred in zip(records, predictions):
        scores = score_pair(pred["prediction"], record.get("final_output", ""))
        rows.append({
            "warc_record_id": pred["warc_record_id"],
            "url": pred["url"],
            "snapshot": pred["snapshot"],
            "n_kept": pred["n_kept"],
            "error": pred["error"],
            **scores,
        })
    return rows, perf_counter() - start


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default=DEFAULT_DATASET,
                        help="benchmark dataset under benchmark/datasets/ (e.g. general, math, code)")
    parser.add_argument("--split", default="dev", help="dev | test | train")
    parser.add_argument("--lang", default="English", help="jusText stoplist language")
    parser.add_argument("--tag", default=None, help="run identifier (default: v<ver>-<sha>)")
    parser.add_argument("--workers", type=int, default=os.cpu_count(),
                        help="parallel jusText workers (1 = serial)")
    parser.add_argument("--limit", type=int, default=None, help="only first N docs (smoke test)")
    parser.add_argument("--skip-run", action="store_true",
                        help="reuse existing predictions; only re-score")
    parser.add_argument("--model", default=None,
                        help="path to a learned classifier (.joblib) for keep/drop decisions")
    parser.add_argument("--allow-test", action="store_true",
                        help="required to evaluate the held-out test split")
    parser.add_argument("--out-dir", default=os.path.join(BENCH_DIR, "runs"))
    args = parser.parse_args()

    if args.split == "test" and not args.allow_test:
        sys.exit("Refusing to touch the held-out test split. Iterate on dev/train. "
                 "Pass --allow-test only for a deliberate, final baseline/test run.")

    tag = args.tag or default_tag()
    run_dir = os.path.join(args.out_dir, tag, args.dataset)
    os.makedirs(run_dir, exist_ok=True)
    pred_path = os.path.join(run_dir, f"{args.split}.predictions.jsonl")
    metrics_path = os.path.join(run_dir, f"{args.split}.metrics.jsonl")
    summary_path = os.path.join(run_dir, f"{args.split}.summary.json")

    records = load_split(args.dataset, args.split)
    if args.limit:
        records = records[: args.limit]

    print(f"tag={tag}  dataset={args.dataset}  split={args.split}  docs={len(records)}  "
          f"lang={args.lang}  workers={args.workers}")

    # ---- run stage ----
    if args.skip_run and os.path.exists(pred_path):
        with open(pred_path, encoding="utf-8") as handle:
            predictions = [json.loads(l) for l in handle]
        if len(predictions) != len(records):
            sys.exit(f"Cached predictions ({len(predictions)}) != docs ({len(records)}); "
                     "drop --skip-run.")
        run_elapsed = None
        print(f"[run]   reused cached predictions ({len(predictions)} docs)")
    else:
        predictions, run_elapsed = run_stage(records, args.lang, args.workers, args.model)
        write_jsonl(pred_path, predictions)
        n_err = sum(1 for p in predictions if p["error"])
        print(f"[run]   {run_elapsed:7.2f}s  "
              f"{1000*run_elapsed/len(records):6.1f} ms/doc  "
              f"{len(records)/run_elapsed:6.1f} docs/s"
              + (f"  ({n_err} errors)" if n_err else ""))

    # ---- score stage ----
    metric_rows, score_elapsed = score_stage(records, predictions)
    write_jsonl(metrics_path, metric_rows)
    print(f"[score] {score_elapsed:7.2f}s  "
          f"{1000*score_elapsed/len(records):6.1f} ms/doc")

    # ---- aggregate ----
    summary = {
        "tag": tag,
        "dataset": args.dataset,
        "split": args.split,
        "n_docs": len(records),
        "config": {
            "justext_version": getattr(justext, "__version__", "unknown"),
            "language": args.lang,
            "paragraph_separator": PARAGRAPH_SEPARATOR,
            "workers": args.workers,
            "model": args.model,
        },
        "timing": {
            "run_seconds": run_elapsed,
            "score_seconds": score_elapsed,
            "run_ms_per_doc": (1000 * run_elapsed / len(records)) if run_elapsed else None,
        },
        "metrics": {
            "rougeL_f": summarize([r["rougeL_f"] for r in metric_rows]),
            "rougeL_p": summarize([r["rougeL_p"] for r in metric_rows]),
            "rougeL_r": summarize([r["rougeL_r"] for r in metric_rows]),
            "lev_distance": summarize([r["lev_distance"] for r in metric_rows]),
            "lev_similarity": summarize([r["lev_similarity"] for r in metric_rows]),
        },
    }
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    m = summary["metrics"]
    print(f"\n=== {tag} / {args.split} ({len(records)} docs) ===")
    print(f"  ROUGE-L  F1   mean {m['rougeL_f']['mean']:.4f}   median {m['rougeL_f']['median']:.4f}")
    print(f"           P/R  mean {m['rougeL_p']['mean']:.4f} / {m['rougeL_r']['mean']:.4f}")
    print(f"  Levenshtein   mean {m['lev_distance']['mean']:.1f} chars   "
          f"similarity mean {m['lev_similarity']['mean']:.4f}")
    print(f"\nwrote:\n  {pred_path}\n  {metrics_path}\n  {summary_path}")


if __name__ == "__main__":
    main()
