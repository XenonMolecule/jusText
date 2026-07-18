"""Optional learned paragraph classifier for jusText.

jusText's default classification is the heuristic cascade in ``core.py``. This module
adds an *opt-in* learned keep/drop decision: a small tree-ensemble (trained offline,
CPU-only) that re-decides each paragraph using the heuristic's own output plus cheap
text features. It runs *after* the heuristic, so it can only refine it.

Design goals (per research log 0003):
  * CPU-only, ~1-2 ms/doc inference (no GPU, no large model).
  * jusText core stays dependency-free: sklearn/joblib are imported lazily and only
    when a model is actually loaded/applied.
  * The feature function lives here and is the single source of truth shared by the
    training script (benchmark/eval/train_classifier.py) and inference.
"""

import math
import re
import zlib

from .core import define_stoplist

_WS = re.compile(r"\s+")

# Heuristic class -> index, used as one-hot features so the model sees the
# heuristic's own decision and can build on it.
_CF = {"good": 0, "neargood": 1, "short": 2, "bad": 3}

FEATURE_NAMES = [
    "log_len", "log_words", "stopword_density", "link_density", "heading",
    "position", "ends_sentence", "avg_word_len", "not_boilerplate",
    "cf_good", "cf_neargood", "cf_short", "cf_bad",
    # DOM-structure features from dom_path (research log 0004): where a paragraph
    # sits in the tree is a strong boilerplate signal the heuristic ignores.
    "dom_depth", "dom_nav", "dom_aside", "dom_header", "dom_footer", "dom_form",
    "dom_list", "dom_table", "dom_main", "dom_blockquote",
    "prev_log_len", "prev_sw", "prev_link", "prev_notboiler",
    "next_log_len", "next_sw", "next_link", "next_notboiler",
]

# Tag groups searched for inside dom_path (lowercased, dot-separated tags).
_DOM_BOILER = {"nav": ("nav",), "aside": ("aside",), "header": ("header",),
               "footer": ("footer",), "form": ("form", "button", "input", "select", "label")}
_DOM_LIST = ("li", "ul", "ol", "dl", "dd", "dt")
_DOM_TABLE = ("table", "td", "th", "tr", "tbody", "thead")
_DOM_MAIN = ("article", "section", "main")


def _dom_features(dom_path):
    tags = dom_path.lower().split(".") if dom_path else []
    s = set(tags)
    return [
        math.log1p(len(tags)),
        float(any(t in s for t in _DOM_BOILER["nav"])),
        float("aside" in s),
        float("header" in s),
        float("footer" in s),
        float(any(t in s for t in _DOM_BOILER["form"])),
        float(any(t in s for t in _DOM_LIST)),
        float(any(t in s for t in _DOM_TABLE)),
        float(any(t in s for t in _DOM_MAIN)),
        float("blockquote" in s),
    ]


def _base_features(paragraph, index, n_paragraphs, stoplist):
    # Only cheap features here -- no per-character Python loops. The char-ratio
    # features (upper/digit) were dropped in 0003: low importance, high cost
    # (they doubled inference time). `avg_word_len`/`ends_sentence` are O(1).
    text = paragraph.text
    length = len(text)
    words = paragraph.words_count
    ends_sentence = 1.0 if text[-1:] in ".!?" else 0.0
    avg_word_len = length / words if words else 0.0
    cf = [0, 0, 0, 0]
    cf[_CF.get(paragraph.cf_class, 3)] = 1
    return [
        math.log1p(length), math.log1p(words),
        paragraph.stopwords_density(stoplist), paragraph.links_density(),
        1.0 if paragraph.heading else 0.0, index / max(1, n_paragraphs - 1),
        ends_sentence, avg_word_len,
        0.0 if paragraph.is_boilerplate else 1.0,
    ] + cf + _dom_features(paragraph.dom_path)


def paragraph_features(paragraphs, stoplist):
    """Return a feature vector (list[float]) per paragraph, including neighbour context.

    Must be called on paragraphs that have already been classified (cf_class /
    class_type set), i.e. after ``classify_paragraphs`` + ``revise_paragraph_classification``.
    Paragraphs with no text are skipped, so this returns ``(features, kept_paragraphs)``.
    """
    stoplist = define_stoplist(stoplist)
    kept = [p for p in paragraphs if p.text.strip()]
    base = [_base_features(p, i, len(kept), stoplist) for i, p in enumerate(kept)]
    zero = [0.0] * len(base[0]) if base else []
    rows = []
    for i, f in enumerate(base):
        prev = base[i - 1] if i > 0 else zero
        nxt = base[i + 1] if i < len(base) - 1 else zero
        # context = (log_len, stopword_density, link_density, not_boilerplate) of neighbours
        rows.append(f + [prev[0], prev[2], prev[3], prev[10],
                         nxt[0], nxt[2], nxt[3], nxt[10]])
    return rows, kept


# _dedup_kept switches from the exact all-pairs scan to the LSH candidate index above this
# many dedup-eligible paragraphs. Typical pages have well under 100, so the exact
# (benchmark-validated) path still handles them; the LSH path exists for the huge
# comment/forum pages where all-pairs fuzz.partial_ratio is quadratic and hangs.
DEDUP_LSH_THRESHOLD = 300
_SHINGLE_W = 5       # char-shingle width
_SAMPLE_MOD = 4      # keep shingle hashes where h % _SAMPLE_MOD == 0 (~25%)
_MIN_FINGERPRINT = 6  # always keep at least the k smallest hashes (short texts)
_LSH_BUCKET_CAP = 64  # a hash shared this widely discriminates nothing -- stop indexing it
_LSH_MAX_VERIFY = 25  # fuzz-verify at most this many top-voted candidates


def _shingle_fingerprint(text):
    """Deterministic sample of the text's char-shingle hashes (its LSH fingerprint).

    The same shingle hashes identically everywhere, so two near-duplicate paragraphs
    sample to overlapping fingerprints, and a paragraph contained in a longer one samples
    to a subset of the container's -- which is what lets the inverted index nominate both
    kinds of duplicate without comparing all pairs. The ``min(...)`` floor keeps the
    fingerprint non-empty for texts too short to have many sampled shingles.
    """
    if len(text) < _SHINGLE_W:
        return {zlib.crc32(text.encode("utf-8"))}
    hashes = {zlib.crc32(text[i:i + _SHINGLE_W].encode("utf-8"))
              for i in range(len(text) - _SHINGLE_W + 1)}
    fingerprint = {h for h in hashes if h % _SAMPLE_MOD == 0}
    fingerprint.update(sorted(hashes)[:_MIN_FINGERPRINT])
    return fingerprint


class ParagraphClassifier:
    """Wraps a trained scikit-learn model and applies it to jusText paragraphs."""

    def __init__(self, model, threshold=0.5, text_vectorizer=None, text_model=None,
                 fasttext_model=None):
        self.model = model
        self.threshold = threshold
        # Optional stacked text model: a model over the paragraph text whose keep-
        # probability is appended as a feature to the struct model. Captures "does this
        # read like kept content" -- the signal structural features miss. Two backends:
        #   * sklearn vectorizer + model (research log 0013)
        #   * fastText (research log 0016): char/word-ngram, trained on 100k docs.
        self.text_vectorizer = text_vectorizer
        self.text_model = text_model
        self.fasttext_model = fasttext_model

    @classmethod
    def load(cls, path, threshold=0.5, fasttext_path=None):
        import joblib  # lazy: only needed when a learned model is used
        payload = joblib.load(path)
        if not isinstance(payload, dict):
            return cls(payload, threshold)
        ft = None
        # fasttext_path argument overrides the path baked into the payload -- the saved path
        # is machine-specific, so a downloaded/distributed model points it at the local copy.
        ft_path = fasttext_path or payload.get("fasttext_path")
        if ft_path:
            import fasttext  # lazy
            fasttext.FastText.eprint = lambda *a, **k: None
            ft = fasttext.load_model(ft_path)
        return cls(payload["model"], payload.get("threshold", threshold),
                   payload.get("text_vectorizer"), payload.get("text_model"), ft)

    def _text_prob(self, texts):
        """Keep-probability per paragraph text from the stacked text model (or None)."""
        import numpy as np  # lazy
        if self.fasttext_model is not None:
            norm = [_WS.sub(" ", t).strip().lower()[:1000] for t in texts]
            labs, probs = self.fasttext_model.predict(norm, k=2)
            return np.array([dict(zip(ls, ps)).get("__label__1", 0.0)
                             for ls, ps in zip(labs, probs)])
        if self.text_model is not None:
            return self.text_model.predict_proba(self.text_vectorizer.transform(texts))[:, 1]
        return None

    def predict_keep(self, paragraphs, stoplist):
        """Return a {paragraph-id: keep_bool} decision for text paragraphs."""
        import numpy as np  # lazy
        rows, kept = paragraph_features(paragraphs, stoplist)
        if not rows:
            return {}
        X = np.asarray(rows)
        tp = self._text_prob([p.text for p in kept])
        if tp is not None:
            # Append the text-model keep-prob plus its previous/next neighbours'
            # probs (research log 0019): content is contiguous, so neighbour keep-
            # probability sharpens block-boundary decisions. Neighbours are within
            # this document's paragraph order (0.0 padding at the edges).
            prev = np.concatenate([[0.0], tp[:-1]])
            nxt = np.concatenate([tp[1:], [0.0]])
            X = np.hstack([X, tp.reshape(-1, 1), prev.reshape(-1, 1), nxt.reshape(-1, 1)])
        proba = self.model.predict_proba(X)[:, 1]
        return {id(p): bool(pp >= self.threshold) for p, pp in zip(kept, proba)}

    def apply(self, paragraphs, stoplist):
        """Override each paragraph's class_type from the model (good=keep, bad=drop).

        Bespoke rule (research log 0012, found by reading extractions): paragraphs inside
        a <pre> are preformatted = intentional content (code, RFCs, ASCII tables) that the
        stopword heuristic wrongly drops. Force-keep them regardless of the model. Helped
        general +0.003 F1 and code +0.014 with no harm to math/science.

        Dedup rule (research log 0018, found via the math/forum duplication case): drop
        later near-duplicate kept paragraphs (forum quotes, re-rendered LaTeX-source
        copies, repeated blocks). The gold never repeats a paragraph; jusText keeps every
        copy. Safe + domain-agnostic; lifted general +0.006 F1 / +0.008 Lev.
        """
        keep = self.predict_keep(paragraphs, stoplist)
        for p in paragraphs:
            if "pre" in p.dom_path.split("."):
                p.class_type = "good"
            elif id(p) in keep:
                p.class_type = "good" if keep[id(p)] else "bad"
        self._dedup_kept(paragraphs, stoplist)
        return paragraphs

    @staticmethod
    def _dedup_kept(paragraphs, stoplist):
        """Mark later near-duplicate kept paragraphs as boilerplate (in document order).

        Comparison normalises curly/straight quotes and drops U+FFFD so the same text in
        different encodings still matches (research log 0030 -- a page that repeats its
        intro with curly vs straight apostrophes was kept twice). Also drops a substantial
        paragraph that is near-exactly *contained* in an earlier, longer kept one (teaser /
        summary excerpts), which the equal-length ratio test misses.

        Dedup targets repeated PROSE (forum quotes, teasers). Code/data lines are skipped --
        they have near-zero stopword density and legitimately repeat (two SQL examples can
        share a first line; loops repeat), so deduping them breaks code (research log 0044).

        Documents with more than ``DEDUP_LSH_THRESHOLD`` dedup-eligible paragraphs switch
        from the exact all-pairs scan (quadratic in paragraphs -- ``partial_ratio`` against
        every earlier longer paragraph hangs huge comment/forum pages) to an LSH candidate
        index: sampled char-shingle fingerprints nominate a bounded number of likely
        matches, and the SAME verification decides. Below the threshold the exact scan is
        unchanged, so benchmark-validated behavior on normal pages is untouched.
        """
        from rapidfuzz import fuzz  # lazy

        def norm(text):
            text = _WS.sub(" ", text).strip().lower()
            for q in "’‘‛":
                text = text.replace(q, "'")
            for q in "“”„":
                text = text.replace(q, '"')
            return text.replace("�", "")

        def is_dup(n, s):
            # score_cutoff lets rapidfuzz reject cheap cases (e.g. length gap) early
            # without changing any >= threshold decision.
            if n == s or fuzz.ratio(n, s, score_cutoff=97) >= 97:
                return True
            # containment: a long paragraph that is a near-exact substring of an
            # earlier, longer kept one (a repeated teaser/excerpt).
            return (len(n) >= 40 and len(s) > len(n)
                    and fuzz.partial_ratio(n, s, score_cutoff=98) >= 98)

        entries = []
        for p in paragraphs:
            if p.class_type != "good":
                continue
            # Don't dedup code/data: verbatim, prose-poor (low stopword density), or
            # punctuation-heavy (code has ~20% non-alphanumeric chars -- quotes/parens/
            # semicolons -- vs ~2-4% for prose). Such paragraphs neither get dropped nor
            # cause later paragraphs to be dropped, so two SQL examples sharing a first
            # line both survive (research log 0044).
            text = p.text
            punct = sum(1 for c in text if not c.isalnum() and not c.isspace())
            if p.verbatim or punct / max(1, len(text)) > 0.13:
                continue
            n = norm(p.text)
            if len(n) < 12:  # keep short lines (could be distinct labels/headers)
                continue
            entries.append((p, n))

        if len(entries) <= DEDUP_LSH_THRESHOLD:
            seen = []
            for p, n in entries:
                if any(is_dup(n, s) for s in seen):
                    p.class_type = "bad"
                else:
                    seen.append(n)
            return

        # LSH path. Candidate generation is an inverted index over each paragraph's
        # fingerprint (a deterministic sample of its char-shingle hashes). A near-duplicate
        # shares most shingles with its original, and a *contained* paragraph's shingles
        # are a subset of its container's, so both surface as candidates through shared
        # sampled hashes. Buckets are capped (a shingle shared by 60+ paragraphs -- " the "
        # etc. -- discriminates nothing) and only the top-voted candidates are verified,
        # so total work stays near-linear.
        seen_texts = []   # unique normalized texts, in document order
        seen_exact = set()
        index = {}        # shingle hash -> ids of seen paragraphs (capped)
        for p, n in entries:
            if n in seen_exact:
                p.class_type = "bad"
                continue
            fingerprint = _shingle_fingerprint(n)
            votes = {}
            for h in fingerprint:
                for sid in index.get(h, ()):
                    votes[sid] = votes.get(sid, 0) + 1
            candidates = sorted(votes, key=lambda sid: (-votes[sid], sid))
            if any(is_dup(n, seen_texts[sid]) for sid in candidates[:_LSH_MAX_VERIFY]):
                p.class_type = "bad"
                continue
            sid = len(seen_texts)
            seen_texts.append(n)
            seen_exact.add(n)
            for h in fingerprint:
                bucket = index.setdefault(h, [])
                if len(bucket) < _LSH_BUCKET_CAP:
                    bucket.append(sid)
