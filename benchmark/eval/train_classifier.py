#!/usr/bin/env python3
"""Train the optional learned paragraph classifier (research log 0003).

Extracts paragraph features (via justext.classifier.paragraph_features) + labels from a
dataset's TRAIN split, fits a small CPU-only RandomForest, and saves it for use with
``run_eval.py --model``. Label = paragraph token-overlap with gold >= --label-overlap.

    python benchmark/eval/train_classifier.py --dataset general
    python benchmark/eval/train_classifier.py --dataset general --trees 30 --depth 12

Keep the model small: inference must stay ~1-2 ms/doc (a hard objective, see 0003).
"""

import argparse
import gzip
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter

_HERE = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(BENCH_DIR))

import justext  # noqa: E402
from justext.classifier import paragraph_features  # noqa: E402
from metrics import tokenize  # noqa: E402
from rapidfuzz import fuzz  # noqa: E402

_WS = re.compile(r"\s+")
_LABEL = "overlap"
_OVERLAP = 0.6

DATASETS_DIR = os.path.join(BENCH_DIR, "datasets")
MODELS_DIR = os.path.join(_HERE, "models")
_STOP = justext.get_stoplist("English")
_FUZZY = 85  # rapidfuzz partial_ratio threshold for the keep label (research log 0012)


def _extract(args):
    """Return (feature_rows, labels) for one doc."""
    html, gold = args
    try:
        paragraphs = justext.justext(html, _STOP)
    except Exception:
        return [], []
    rows, kept = paragraph_features(paragraphs, _STOP)
    # Label methods (research log 0012):
    #  - "overlap": >= _OVERLAP of paragraph tokens present in gold (best for the
    #    structural RF -- easier to predict from features; shipped).
    #  - "fuzzy": paragraph text fuzzily matches a substring of gold (rapidfuzz
    #    partial_ratio). Cleaner label (oracle 0.944) but harder for the struct model;
    #    useful for the text-stack experiments.
    if _LABEL == "fuzzy":
        gnorm = _WS.sub(" ", gold).strip().lower()
        labels = [1 if (len(p.text.strip()) >= 3 and
                        fuzz.partial_ratio(_WS.sub(" ", p.text).strip().lower(), gnorm) >= _FUZZY)
                  else 0 for p in kept]
    else:
        gset = set(tokenize(gold))
        labels = []
        for p in kept:
            toks = tokenize(p.text)
            labels.append(1 if toks and sum(t in gset for t in toks) / len(toks) >= _OVERLAP else 0)
    return rows, labels


def load_split(dataset, split):
    path = os.path.join(DATASETS_DIR, dataset, f"{split}.jsonl.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        recs = [json.loads(l) for l in fh if l.strip()]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        per = list(ex.map(_extract, [(r["html"], r["final_output"]) for r in recs], chunksize=16))
    X = [row for rows, _ in per for row in rows]
    y = [lab for _, labs in per for lab in labs]
    return X, y


def main():
    global _FUZZY, _LABEL, _OVERLAP
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="general")
    ap.add_argument("--trees", type=int, default=30)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--min-leaf", type=int, default=20)
    ap.add_argument("--label", choices=["overlap", "fuzzy"], default="overlap",
                    help="keep-label method (overlap=best for struct model; fuzzy=cleaner)")
    ap.add_argument("--label-overlap", type=float, default=0.6)
    ap.add_argument("--fuzzy", type=int, default=85,
                    help="rapidfuzz partial_ratio threshold for fuzzy label")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    _FUZZY = args.fuzzy; _LABEL = args.label; _OVERLAP = args.label_overlap

    import numpy as np
    import joblib
    from sklearn.ensemble import RandomForestClassifier

    print(f"extracting {args.dataset}/train ...", flush=True)
    t0 = perf_counter()
    X, y = load_split(args.dataset, "train")
    X = np.asarray(X); y = np.asarray(y)
    print(f"  {len(y)} paragraphs, positive rate {y.mean():.3f}, {perf_counter()-t0:.1f}s")

    clf = RandomForestClassifier(
        n_estimators=args.trees, max_depth=args.depth, min_samples_leaf=args.min_leaf,
        n_jobs=os.cpu_count(), random_state=0,
    )
    clf.fit(X, y)

    os.makedirs(MODELS_DIR, exist_ok=True)
    out = args.out or os.path.join(MODELS_DIR, f"{args.dataset}.joblib")
    joblib.dump({"model": clf, "threshold": 0.5,
                 "config": {"trees": args.trees, "depth": args.depth,
                            "min_leaf": args.min_leaf, "fuzzy": args.fuzzy}},
                out, compress=3)
    size_kb = os.path.getsize(out) / 1024
    print(f"saved {out}  ({size_kb:.0f} KB)")
    imp = sorted(zip(__import__("justext.classifier", fromlist=["FEATURE_NAMES"]).FEATURE_NAMES,
                     clf.feature_importances_), key=lambda kv: -kv[1])
    print("top features:", [(n, round(float(v), 3)) for n, v in imp[:6]])


if __name__ == "__main__":
    main()
