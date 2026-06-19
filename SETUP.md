# Setup — improved jusText fork

This is an improved fork of [jusText](https://github.com/miso-belica/jusText) for main-content
/ boilerplate extraction from HTML. On the held-out test set (general, 1000 docs) it scores
**0.889 ROUGE-L F1 / 0.826 Levenshtein** vs stock jusText's 0.773 / 0.690.

- **Code:** https://github.com/XenonMolecule/jusText
- **Model (fastText tier):** https://huggingface.co/MichaelR207/justext-classifier (public)

## Install

```bash
# Tier A — bundled 3MB sklearn model (F1 0.866). Works offline, no extra setup.
pip install "git+https://github.com/XenonMolecule/jusText"

# Tier B — fastText model (F1 0.886). ~780MB, auto-downloaded from HuggingFace on first use.
pip install "jusText[fasttext] @ git+https://github.com/XenonMolecule/jusText"
```

## Use

```python
import justext
stoplist = justext.get_stoplist("English")
paragraphs = justext.justext(html, stoplist)          # auto-selects the best model installed
text = "\n\n".join(p.text for p in paragraphs if not p.is_boilerplate)
```

The model tier is auto-resolved: **fastText → bundled 3MB → heuristic**, degrading gracefully
(missing dep / offline always falls back, never crashes). `model=None` forces the heuristic.

## Getting the fastText tier working (the main thing to set up)

1. Install with the `[fasttext]` extra (installs `fasttext` + `huggingface_hub`).
2. First `justext.justext(...)` call (or `justext.download_fasttext()`) pulls
   `general-ftstack.joblib` + `general_ft.bin` (~780MB total) from
   `MichaelR207/justext-classifier` into `~/.cache/justext`. Cached after that.

```python
import justext
joblib_path, fasttext_path = justext.download_fasttext()   # pre-fetch (optional)
m = justext.get_model()
assert m is not None and m.fasttext_model is not None      # confirms fastText tier active
```

### Environment knobs

| Variable | Effect |
|---|---|
| `JUSTEXT_MODEL` | `fasttext` \| `sklearn` \| `heuristic` \| `auto` (default) |
| `JUSTEXT_NO_DOWNLOAD` | skip the download, use the bundled 3MB model |
| `JUSTEXT_HF_REPO` | use a different model repo (default `MichaelR207/justext-classifier`) |
| `JUSTEXT_CACHE` | relocate the download cache (default `~/.cache/justext`) |

## Gotchas

- **`fasttext` build:** needs a C++ toolchain; on some setups use `pip install fasttext-wheel`.
- **scikit-learn version:** the bundled model was trained on sklearn 1.5; a very different
  major version only warns (and falls back if unpickling ever fails). Pin `scikit-learn~=1.5`
  if you want to silence the warning.
- **Verify the tier in use:** `type(justext.get_model()).__name__` is `ParagraphClassifier`
  for the model tiers, `NoneType` for heuristic; `.fasttext_model is not None` ⇒ fastText.

## Repo internals (if they need to dig in)

- `justext/core.py` — extraction + all the structural transforms (forum/FAQ/comment
  role-transforms, code, URL/mojibake repair).
- `justext/_models.py` — model resolution + HuggingFace download.
- `justext/classifier.py` — `ParagraphClassifier` (sklearn + optional fastText stack).
- `benchmark/eval/run_eval.py` — scoring harness (`--dataset`, `--split`, `--model`,
  `--allow-test`); `research_log/` documents every change and its measured effect.
