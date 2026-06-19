# WARC → HTML decoding: recommendations

Hand-off notes for the pipeline that extracts HTML from WARC records before jusText sees it.
Diagnosed from the general/dev set: **88 / 1000 docs contain `�` (U+FFFD)** and the body is
sometimes truncated. Both are decode-stage bugs, not jusText.

## The bug

Every `�` in our data is a real source character that got destroyed:

| stored | was | character |
|---|---|---|
| `Ghana�s`, `user�s` | `'s` | curly apostrophe U+2019 |
| `pi� spinte` | `più` | à-grave (cp1252/latin-1) |
| `�300` | `£300` | pound sign U+00A3 |
| `T�m�` | `Tämä` | Finnish ä |

**82 of the 88 corrupted docs declare no `<meta charset>`.** With no charset in the markup,
a decoder that only looks at the meta tag and then falls back to a fixed codec with
`errors="replace"` turns every non-ASCII byte into `�`.

### Why this matters that it's `�` specifically

`U+FFFD` is the Unicode *replacement character*. It is written **after** the original byte
has already been thrown away. Once it's in the string, **the source is unrecoverable** — no
downstream `ftfy`/repair can bring it back. The fix has to happen at decode time, and the
existing corrupted rows can only be fixed by **re-extracting from the WARCs**.

(The separate, smaller case — 6 docs with `Ã©` / `â€™` "mojibake" — *is* recoverable, because
those bytes survived intact; `ftfy.fix_text()` or `s.encode("latin-1").decode("utf-8")`
repairs them. That happens when UTF-8 bytes are decoded as cp1252 *without* `errors=replace`.)

## Rule 1 — decode the raw bytes once, never re-decode a `str`

Take the WARC **response** record, split off the HTTP header block on the first `\r\n\r\n`,
and decode the *payload bytes*. Never `.encode().decode()` a string you already have, and
never decode twice — that's how you manufacture both `�` and `Ã©`.

## Rule 2 — resolve the charset in WHATWG order (don't trust meta alone)

Because 82/88 of our failures have no meta charset, meta-only resolution is the core defect.
Use this precedence:

1. **BOM** sniff (UTF-8/UTF-16 byte-order mark) → authoritative.
2. **WARC/HTTP `Content-Type` header** `charset=` (the record stores the original response
   header — use it; this is what the meta tag is *missing*).
3. **`<meta charset>` / `<meta http-equiv>`** in the first ~1024 bytes.
4. **Statistical detection** on the bytes: `charset-normalizer` (preferred) or `chardet`.
5. **Fallback to `windows-1252`, never `ascii`/strict `latin-1`** — cp1252 decodes *any*
   byte (no errors, no `�`), and it's the correct guess for the legacy Western pages that
   dominate this failure set. Crucially, **drop `errors="replace"`** from the primary path;
   `�` should never be produced.

## Rule 3 — don't hand-roll it; use a library that implements the algorithm

Any of these does steps 1–5 correctly:

```python
# Option A — w3lib (Scrapy's), purpose-built for exactly "HTTP header + bytes -> unicode"
from w3lib.encoding import html_to_unicode
detected_encoding, html = html_to_unicode(
    content_type_header,   # e.g. "text/html; charset=..." from the WARC HTTP headers, or None
    raw_payload_bytes,
    auto_detect_fun=lambda b: charset_normalizer.from_bytes(b).best().encoding,
)

# Option B — charset-normalizer alone (when you don't have the header handy)
import charset_normalizer
html = str(charset_normalizer.from_bytes(raw_payload_bytes).best())

# Option C — BeautifulSoup's UnicodeDammit (bundles cchardet)
from bs4 import UnicodeDammit
html = UnicodeDammit(raw_payload_bytes, is_html=True).unicode_markup
```

`resiliparse.parse.encoding` (from the Common Crawl ecosystem) is also a good fit if you're
already in that stack.

## Rule 4 — verify, and fail loudly

After decoding, assert the output is clean before storing:

```python
if "�" in html:
    # decode failed — log url + WARC id, re-derive; do NOT ship the row
    ...
```

A scan for `�` across the corpus is a cheap regression check: a correct pipeline
produces **zero**.

## Rule 5 — feed jusText the whole decoded page

Separately from encoding: don't pre-strip the page to a body fragment (in our set only
9/1000 stored docs are still full pages, and 12/1000 have the body truncated out entirely).
jusText does its own boilerplate removal and wants the full `<html>` document — over-eager
pre-extraction is where the body-truncation cases come from.

## Already-corrupted data

- `�` (U+FFFD) rows: **re-extract from WARC** (unrecoverable in place).
- `Ã©`/`â€™` rows: recoverable now with `ftfy.fix_text()`.
