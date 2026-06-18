#!/usr/bin/env python3
"""Rebuild justext/_char_repair.py (research log 0029).

Learns a (2-chars-before, 2-chars-after) -> original-char table for repairing U+FFFD
replacement characters, by aligning corrupted general/train html to the gold. Keeps only
high-confidence contexts (>= MIN_COUNT samples, >= MIN_FRAC agreement). U+FFFD is a lossy
decode artefact (a cp1252/Latin-1 byte decoded as utf-8 with errors='replace'); the byte
is gone, but the surrounding context usually pins the original char (apostrophes in
contractions dominate). High-precision only -- an unknown context is left as U+FFFD.

    python benchmark/eval/build_char_repair.py
"""
import gzip, json, os, re
from collections import defaultdict, Counter

MIN_COUNT = 3
MIN_FRAC = 0.8
HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
OUT = os.path.join(os.path.dirname(BENCH), "justext", "_char_repair.py")


MIN_COUNT_1 = 5   # 1-char fallback tier needs more support
MIN_FRAC_1 = 0.85


def _confident(ctx, min_count, min_frac):
    table = {}
    for k, cnt in ctx.items():
        c, n = cnt.most_common(1)[0]
        if n >= min_count and n / sum(cnt.values()) >= min_frac:
            table[k] = c
    return table


def main():
    path = os.path.join(BENCH, "datasets", "general", "train.jsonl.gz")
    recs = [json.loads(l) for l in gzip.open(path, "rt", encoding="utf-8") if l.strip()]
    ctx2, ctx1 = defaultdict(Counter), defaultdict(Counter)
    for r in recs:
        h, g = r["html"], re.sub(r"\s+", " ", r["final_output"])
        if "�" not in h:
            continue
        for m in re.finditer(r"(..)�(..)", h):
            a, b = m.group(1), m.group(2)
            mm = re.search(re.escape(a) + r"(.)" + re.escape(b), g)
            if mm and mm.group(1) != "�" and ord(mm.group(1)) > 127:
                ctx2[(a, b)][mm.group(1)] += 1
        for m in re.finditer(r"(.)�(.)", h):
            a, b = m.group(1), m.group(2)
            mm = re.search(re.escape(a) + r"(.)" + re.escape(b), g)
            if mm and mm.group(1) != "�" and ord(mm.group(1)) > 127:
                ctx1[(a, b)][mm.group(1)] += 1
    table2 = _confident(ctx2, MIN_COUNT, MIN_FRAC)
    table1 = _confident(ctx1, MIN_COUNT_1, MIN_FRAC_1)
    lines = ["# -*- coding: utf-8 -*-",
             '"""Auto-generated U+FFFD repair tables (research log 0029, 0036).',
             "Map a context around a replacement char to the most-likely original character,",
             "learned from general/train by aligning corrupted html to the gold. REPAIR_TABLE is",
             "the precise (2-before, 2-after) tier (>=3 samples, >=80%); REPAIR_TABLE_1 is a",
             "(1-before, 1-after) fallback (>=5 samples, >=85%) that recovers curly quotes/dashes",
             "the 2-char tier misses. Apply 2-char first, then 1-char. Rebuild:",
             "benchmark/eval/build_char_repair.py",
             '"""', "", "REPAIR_TABLE = {"]
    for (a, b), c in sorted(table2.items()):
        lines.append("    (%r, %r): %r," % (a, b, c))
    lines.append("}")
    lines.append("")
    lines.append("REPAIR_TABLE_1 = {")
    for (a, b), c in sorted(table1.items()):
        lines.append("    (%r, %r): %r," % (a, b, c))
    lines.append("}")
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s with %d (2-char) + %d (1-char) contexts" % (OUT, len(table2), len(table1)))


if __name__ == "__main__":
    main()
