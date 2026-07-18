import random
import time

import pytest

pytest.importorskip("rapidfuzz")

from justext import classifier
from justext.classifier import ParagraphClassifier


class FakeParagraph(object):
    def __init__(self, text, class_type="good", verbatim=False):
        self.text = text
        self.class_type = class_type
        self.verbatim = verbatim


WORDS = ("the quick brown fox jumps over a lazy dog while many small birds "
         "watch from tall green trees near this old quiet river bank today "
         "because every single moment brings some new strange wonder here").split()


def make_texts(count, words_per_text=18, seed=1234):
    rng = random.Random(seed)
    return [" ".join(rng.choice(WORDS) for _ in range(words_per_text))
            for _ in range(count)]


def dedup(paragraphs):
    ParagraphClassifier._dedup_kept(paragraphs, "English")
    return paragraphs


def build_document(n_distinct):
    """Distinct prose paragraphs plus one of each duplicate category."""
    texts = make_texts(n_distinct)
    paragraphs = [FakeParagraph(t) for t in texts]
    long_text = " ".join(make_texts(1, words_per_text=60, seed=999))
    paragraphs.append(FakeParagraph(long_text))
    dup_indexes = []
    # exact duplicate
    paragraphs.append(FakeParagraph(texts[3]))
    dup_indexes.append(len(paragraphs) - 1)
    # near-duplicate (curly apostrophe + one changed char)
    paragraphs.append(FakeParagraph(texts[5].replace(" ", "’", 1)))
    dup_indexes.append(len(paragraphs) - 1)
    # containment: a chunk of the long paragraph repeated as a teaser
    paragraphs.append(FakeParagraph(long_text[:80]))
    dup_indexes.append(len(paragraphs) - 1)
    # and one more distinct paragraph after the dups
    paragraphs.append(FakeParagraph(" ".join(make_texts(1, seed=777))))
    return paragraphs, dup_indexes


def test_small_document_drops_all_duplicate_kinds():
    paragraphs, dup_indexes = build_document(50)
    assert len(paragraphs) <= classifier.DEDUP_LSH_THRESHOLD
    dedup(paragraphs)

    assert [i for i, p in enumerate(paragraphs) if p.class_type == "bad"] == dup_indexes


def test_large_document_drops_all_duplicate_kinds():
    paragraphs, dup_indexes = build_document(classifier.DEDUP_LSH_THRESHOLD + 100)
    dedup(paragraphs)

    assert [i for i, p in enumerate(paragraphs) if p.class_type == "bad"] == dup_indexes


def test_lsh_path_matches_exact_path(monkeypatch):
    exact, dup_indexes = build_document(150)
    lsh, _ = build_document(150)

    dedup(exact)
    monkeypatch.setattr(classifier, "DEDUP_LSH_THRESHOLD", 0)
    dedup(lsh)

    assert [p.class_type for p in lsh] == [p.class_type for p in exact]
    assert [i for i, p in enumerate(lsh) if p.class_type == "bad"] == dup_indexes


def test_verbatim_and_code_still_skipped_on_large_documents():
    paragraphs = [FakeParagraph(t) for t in make_texts(classifier.DEDUP_LSH_THRESHOLD + 10)]
    code = 'result = compute(x); print("total=%d" % result); return {"a": [1, 2]}'
    paragraphs.append(FakeParagraph(code))
    paragraphs.append(FakeParagraph(code))
    paragraphs.append(FakeParagraph("some repeated verbatim block", verbatim=True))
    paragraphs.append(FakeParagraph("some repeated verbatim block", verbatim=True))
    dedup(paragraphs)

    assert all(p.class_type == "good" for p in paragraphs[-4:])


def test_huge_document_completes_quickly():
    # 4000 paragraphs, every fourth a duplicate of an earlier one: the all-pairs
    # partial_ratio scan takes minutes on this; the LSH path must stay fast.
    texts = make_texts(3000, words_per_text=40)
    paragraphs = []
    for i, t in enumerate(texts):
        paragraphs.append(FakeParagraph(t))
        if i % 3 == 0:
            paragraphs.append(FakeParagraph(texts[i // 2]))
    start = time.time()
    dedup(paragraphs)
    elapsed = time.time() - start

    assert elapsed < 30
    dropped = sum(1 for p in paragraphs if p.class_type == "bad")
    assert dropped >= 900
