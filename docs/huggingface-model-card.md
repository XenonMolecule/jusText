---
license: bsd-2-clause
library_name: justext
tags:
  - boilerplate-removal
  - web-extraction
  - text-extraction
  - justext
  - fasttext
language:
  - en
---

# justext-classifier

The learned paragraph classifier for the improved [jusText fork](https://github.com/XenonMolecule/jusText)
— a boilerplate-removal tool that extracts the main content from an HTML page and drops
navigation, sidebars, footers, and other chrome.

This repo hosts the **highest-quality tier**: a scikit-learn paragraph classifier whose
features are stacked with a [fastText](https://fasttext.cc/) keep-probability model. The fork
auto-downloads it on first use; you normally don't fetch it by hand.

## Files

| File | Size | What it is |
|---|--:|---|
| `general-ftstack.joblib` | ~9 MB | scikit-learn classifier (RandomForest over structural + text features) |
| `general_ft.bin` | ~770 MB | fastText char/word-ngram model providing the stacked keep-probability feature |

## Quality (general dev set: token ROUGE-L F1 / char Levenshtein similarity)

| Tier | F1 | Lev | Footprint |
|---|--:|--:|---|
| heuristic (no model) | 0.821 | 0.741 | none |
| bundled 3 MB sklearn | 0.866 | 0.795 | ships in the wheel |
| **this model (fastText stack)** | **0.886** | **0.823** | this repo (~780 MB) |

For reference, stock upstream jusText scores ~0.76 on the same set; the fork's structural
fixes (forum/FAQ/comment role-transforms, code formatting, URL/mojibake repair, …) lift every
tier well above that even before the learned classifier.

## Usage

Install the fork with the fastText extra, then just call `justext` — the model is fetched and
cached (`~/.cache/justext`) on first use:

```bash
pip install "jusText[fasttext] @ git+https://github.com/XenonMolecule/jusText"
```

```python
import justext

stoplist = justext.get_stoplist("English")
paragraphs = justext.justext(html, stoplist)          # auto-uses this model
content = "\n\n".join(p.text for p in paragraphs if not p.is_boilerplate)
```

Fetch explicitly (e.g. to pre-warm the cache):

```python
import justext
joblib_path, fasttext_path = justext.download_fasttext()   # pulls both files here
```

### Tier / behaviour knobs (environment variables)

| Variable | Effect |
|---|---|
| `JUSTEXT_MODEL` | `fasttext` \| `sklearn` \| `heuristic` \| `auto` (default) |
| `JUSTEXT_NO_DOWNLOAD` | set to skip the download and use the bundled 3 MB model |
| `JUSTEXT_HF_REPO` | point at a different repo (default `XenonMolecule/justext-classifier`) |
| `JUSTEXT_CACHE` | override the download cache directory |

If `fasttext` isn't installed, or the download fails, the fork degrades gracefully to the
bundled 3 MB model and then to the heuristic classifier — it always works offline.

## How it was trained

- **Structural classifier**: RandomForest over jusText's per-paragraph heuristic features
  (link density, stopword density, length, tag context) plus neighbour signals.
- **Stacked text model**: a fastText classifier trained on ~100k labelled paragraphs; its
  keep-probability is appended as a feature to the structural model.
- Tuned on an LLM-distilled main-content extraction benchmark (`general` split).

## License

BSD 2-Clause, same as jusText. See the [fork repository](https://github.com/XenonMolecule/jusText).
