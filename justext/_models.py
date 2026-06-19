# -*- coding: utf-8 -*-

"""Model resolution for the improved jusText fork.

Tiers, best to worst (general/dev F1 / Lev):
  * fastText stack  0.886 / 0.823 -- ~780 MB, downloaded once from HuggingFace
  * 3 MB sklearn    0.866 / 0.795 -- bundled in the wheel (needs scikit-learn)
  * heuristic       0.821 / 0.741 -- no model, no extra deps (still > stock jusText)

`get_model()` returns the best one available and caches it. The fastText tier is the default;
it downloads the binary from HuggingFace on first use (set ``JUSTEXT_NO_DOWNLOAD=1`` to skip,
or ``JUSTEXT_MODEL=sklearn|heuristic|fasttext`` to force a tier). All failures fall back
gracefully to the next tier, so jusText always works offline.
"""

from __future__ import absolute_import

import os
import sys

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_MODEL = os.path.join(_PKG_DIR, "models", "general.joblib")

# HuggingFace repo holding the large fastText-stacked model. Override with $JUSTEXT_HF_REPO.
HF_REPO = os.environ.get("JUSTEXT_HF_REPO", "MichaelR207/justext-classifier")
_FTSTACK_FILE = "general-ftstack.joblib"
_FASTTEXT_FILE = "general_ft.bin"

_CACHED = "unset"  # process-wide cache for get_model()


def cache_dir():
    base = os.environ.get(
        "JUSTEXT_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "justext"))
    try:
        os.makedirs(base)
    except OSError:
        pass
    return base


def download_fasttext(repo=None, force=False):
    """Download the fastText-stacked model (~780 MB) from HuggingFace into the cache.

    Returns ``(ftstack_joblib_path, fasttext_bin_path)``. Uses ``huggingface_hub`` if present
    (resumable, deduplicated), else a plain urllib download to the cache directory.
    """
    repo = repo or HF_REPO
    cache = cache_dir()
    try:
        from huggingface_hub import hf_hub_download
        joblib_path = hf_hub_download(repo_id=repo, filename=_FTSTACK_FILE,
                                      cache_dir=cache, force_download=force)
        ft_path = hf_hub_download(repo_id=repo, filename=_FASTTEXT_FILE,
                                  cache_dir=cache, force_download=force)
        return joblib_path, ft_path
    except ImportError:
        pass
    try:
        from urllib.request import urlretrieve
    except ImportError:  # py2
        from urllib import urlretrieve
    out = {}
    for fname in (_FTSTACK_FILE, _FASTTEXT_FILE):
        dst = os.path.join(cache, fname)
        if force or not os.path.exists(dst):
            url = "https://huggingface.co/%s/resolve/main/%s" % (repo, fname)
            sys.stderr.write("justext: downloading %s -> %s\n" % (url, dst))
            sys.stderr.flush()
            urlretrieve(url, dst)
        out[fname] = dst
    return out[_FTSTACK_FILE], out[_FASTTEXT_FILE]


def _load_fasttext_stack():
    import fasttext  # noqa: F401 -- fail fast (before a 780MB download) if not installed
    from .classifier import ParagraphClassifier
    joblib_path, ft_path = download_fasttext()
    return ParagraphClassifier.load(joblib_path, fasttext_path=ft_path)


def _load_bundled():
    from .classifier import ParagraphClassifier
    import sklearn  # noqa: F401 -- ensure the dep is present before unpickling
    return ParagraphClassifier.load(BUNDLED_MODEL)


def get_model():
    """Return the best available ParagraphClassifier, or None for the heuristic path.

    Cached after the first call. Honors ``JUSTEXT_MODEL`` (fasttext|sklearn|heuristic|auto)
    and ``JUSTEXT_NO_DOWNLOAD``. Never raises -- it degrades to the next tier on any failure.
    """
    global _CACHED
    if _CACHED != "unset":
        return _CACHED
    _CACHED = _resolve()
    return _CACHED


def _have(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def _resolve():
    mode = os.environ.get("JUSTEXT_MODEL", "auto").lower()
    if mode == "heuristic":
        return None
    # fastText tier: only on `auto` when the optional fasttext dep is installed (the
    # `[fasttext]` extra), or when explicitly forced with JUSTEXT_MODEL=fasttext. This keeps
    # the default 3MB install quiet -- no download attempt, no warning.
    want_ft = (mode == "fasttext") or (mode == "auto" and _have("fasttext"))
    if want_ft and not os.environ.get("JUSTEXT_NO_DOWNLOAD"):
        try:
            return _load_fasttext_stack()
        except Exception as exc:  # noqa: BLE001 -- any failure -> next tier
            sys.stderr.write(
                "justext: fastText model unavailable (%s); falling back to the bundled 3MB "
                "model. Set JUSTEXT_HF_REPO to your HuggingFace repo, or JUSTEXT_MODEL=sklearn "
                "to silence.\n" % exc)
    try:
        return _load_bundled()
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(
            "justext: 3MB model unavailable (%s); using the heuristic classifier "
            "(pip install scikit-learn for higher quality).\n" % exc)
    return None
