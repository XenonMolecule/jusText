#!/usr/bin/env python3
"""Ceiling / failure-taxonomy analysis (research log 0006).

For a cached run, this re-runs jusText to recover *all* paragraphs, computes the
**paragraph-selection oracle** per doc (keep paragraphs whose tokens are >= --overlap
present in gold), and classifies every doc by *why* it falls short — separating what a
better model could fix from what it never could:

  GOLD_NOISE     gold is the teacher's meta-commentary/reasoning, not extracted text
                 (e.g. "The user wants to extract...", "The HTML appears to be...").
                 No extractor can match it -- it caps the score artificially.
  METHOD_LIMITED oracle F1 < --low even with perfect selection: segmentation/formatting
                 can't represent this gold. Needs different inputs, not a better model.
  MODEL_LIMITED  oracle is high but the model is >= --margin worse: FIXABLE headroom
                 (the right paragraphs exist; the classifier just picks wrong).
  OK             model is already near the oracle.

Usage:
    python benchmark/eval/ceiling.py --tag 0004-dom-features --dataset general --split dev
"""

import argparse
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))

import justext  # noqa: E402
from analysis import load_run  # noqa: E402
from metrics import tokenize, rouge_l  # noqa: E402

_STOP = justext.get_stoplist("English")
_OVERLAP = 0.6

# Tight detector for teacher meta-commentary / abstention in the gold's opening.
_META = re.compile(
    r"^(.{0,120})?\b("
    r"the user wants|extract (the )?main content|there is no main content|"
    r"the (given )?html (is|appears|content)|the main content area|"
    r"i need to (extract|find)|the (page|document|content) (appears to be|is a generic)|"
    r"this (html|page|document) (is|appears|contains) a"
    r")", re.I)


def _oracle_f1(args):
    html, gold = args
    try:
        paras = justext.justext(html, _STOP)
    except Exception:
        return 0.0
    gset = set(tokenize(gold))
    kept = [p.text for p in paras
            if (lambda t: t and sum(w in gset for w in t) / len(t) >= _OVERLAP)(tokenize(p.text))]
    return rouge_l("\n\n".join(kept), gold)[2]


def main():
    global _OVERLAP
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=None)
    ap.add_argument("--dataset", default="general")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--overlap", type=float, default=0.6, help="oracle keep threshold")
    ap.add_argument("--low", type=float, default=0.7, help="oracle F1 below this = method-limited")
    ap.add_argument("--margin", type=float, default=0.15, help="oracle-model gap = model-limited")
    ap.add_argument("--examples", type=int, default=3)
    args = ap.parse_args()
    _OVERLAP = args.overlap

    run = load_run(args.tag, args.split, args.dataset)
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        oracle = list(ex.map(_oracle_f1, [(d.html, d.gold) for d in run.docs], chunksize=16))

    buckets = {"GOLD_NOISE": [], "METHOD_LIMITED": [], "MODEL_LIMITED": [], "OK": []}
    for d, orc in zip(run.docs, oracle):
        if _META.search(d.gold[:160] or ""):
            buckets["GOLD_NOISE"].append((d, orc))
        elif orc < args.low:
            buckets["METHOD_LIMITED"].append((d, orc))
        elif orc - d.score >= args.margin:
            buckets["MODEL_LIMITED"].append((d, orc))
        else:
            buckets["OK"].append((d, orc))

    n = len(run.docs)
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0
    print(f"{run.tag} / {run.dataset}/{run.split}  ({n} docs)")
    print(f"mean model F1={mean([d.score for d in run.docs]):.4f}  "
          f"mean oracle F1={mean(oracle):.4f}  ceiling gap={mean(oracle)-mean([d.score for d in run.docs]):.4f}")
    print(f"\n{'bucket':<16}{'n':>5}{'%':>6}{'model_F1':>10}{'oracle_F1':>10}{'fixable_headroom':>18}")
    for name, items in buckets.items():
        if not items:
            continue
        mf = mean([d.score for d, _ in items])
        of = mean([o for _, o in items])
        # headroom = what reaching the oracle on these docs would add to the overall mean
        head = sum(max(0, o - d.score) for d, o in items) / n
        print(f"{name:<16}{len(items):>5}{100*len(items)/n:>5.1f}%{mf:>10.3f}{of:>10.3f}{head:>18.4f}")

    for name in ("GOLD_NOISE", "METHOD_LIMITED", "MODEL_LIMITED"):
        items = sorted(buckets[name], key=lambda x: x[0].score)[: args.examples]
        if items:
            print(f"\n--- {name} examples ---")
            for d, orc in items:
                print(f"  F1={d.score:.2f} oracle={orc:.2f} {d.url[:45]:<45} gold: {d.gold[:70]!r}")


if __name__ == "__main__":
    main()
