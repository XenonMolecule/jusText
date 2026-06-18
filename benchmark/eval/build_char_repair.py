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


def main():
    path = os.path.join(BENCH, "datasets", "general", "train.jsonl.gz")
    recs = [json.loads(l) for l in gzip.open(path, "rt", encoding="utf-8") if l.strip()]
    ctx = defaultdict(Counter)
    for r in recs:
        h, g = r["html"], re.sub(r"\s+", " ", r["final_output"])
        if "�" not in h:
            continue
        for m in re.finditer(r"(..)�(..)", h):
            a, b = m.group(1), m.group(2)
            mm = re.search(re.escape(a) + r"(.)" + re.escape(b), g)
            if mm and mm.group(1) != "�" and ord(mm.group(1)) > 127:
                ctx[(a, b)][mm.group(1)] += 1
    table = {}
    for k, cnt in ctx.items():
        c, n = cnt.most_common(1)[0]
        if n >= MIN_COUNT and n / sum(cnt.values()) >= MIN_FRAC:
            table[k] = c
    lines = ["# -*- coding: utf-8 -*-",
             '"""Auto-generated U+FFFD repair table (research log 0029).',
             "Maps a (2-chars-before, 2-chars-after) context around a replacement char to the",
             "most-likely original character, learned from general/train by aligning corrupted",
             "html to the gold (kept only contexts with >=3 samples and >=80% agreement).",
             "Rebuild: benchmark/eval/build_char_repair.py",
             '"""', "", "REPAIR_TABLE = {"]
    for (a, b), c in sorted(table.items()):
        lines.append("    (%r, %r): %r," % (a, b, c))
    lines.append("}")
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s with %d contexts" % (OUT, len(table)))


if __name__ == "__main__":
    main()
