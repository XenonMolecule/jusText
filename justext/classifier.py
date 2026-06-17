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

from .core import define_stoplist

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


class ParagraphClassifier:
    """Wraps a trained scikit-learn model and applies it to jusText paragraphs."""

    def __init__(self, model, threshold=0.5):
        self.model = model
        self.threshold = threshold

    @classmethod
    def load(cls, path, threshold=0.5):
        import joblib  # lazy: only needed when a learned model is used
        payload = joblib.load(path)
        if isinstance(payload, dict):
            return cls(payload["model"], payload.get("threshold", threshold))
        return cls(payload, threshold)

    def predict_keep(self, paragraphs, stoplist):
        """Return a {paragraph-id: keep_bool} decision for text paragraphs."""
        import numpy as np  # lazy
        rows, kept = paragraph_features(paragraphs, stoplist)
        if not rows:
            return {}
        proba = self.model.predict_proba(np.asarray(rows))[:, 1]
        return {id(p): bool(pp >= self.threshold) for p, pp in zip(kept, proba)}

    def apply(self, paragraphs, stoplist):
        """Override each paragraph's class_type from the model (good=keep, bad=drop)."""
        keep = self.predict_keep(paragraphs, stoplist)
        for p in paragraphs:
            if id(p) in keep:
                p.class_type = "good" if keep[id(p)] else "bad"
        return paragraphs
