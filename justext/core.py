# -*- coding: utf-8 -*-

"""
Copyright (c) 2011 Jan Pomikalek

This software is licensed as described in the file LICENSE.rst.
"""

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import copy
import re
import lxml.html
import lxml.sax

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

# lxml 5.2 split the HTML cleaner into a standalone ``lxml_html_clean`` package; older lxml
# still ships it at ``lxml.html.clean``. Try the new location first, fall back to the old one.
try:
    from lxml_html_clean import Cleaner
except ImportError:
    from lxml.html.clean import Cleaner
from xml.sax.handler import ContentHandler
from .paragraph import Paragraph
from ._compat import unicode, ignored, unescape
from .utils import is_blank


# Classification thresholds. Retuned (research log 0002) against the LLM-distilled
# extraction benchmark; the original CleanEval-era values were 70/200/0.30/0.32 and
# dropped too much content (whole clean English docs collapsed to boilerplate because
# no paragraph cleared the strict 200-char "good" bar).
MAX_LINK_DENSITY_DEFAULT = 0.2
LENGTH_LOW_DEFAULT = 40
LENGTH_HIGH_DEFAULT = 60
STOPWORDS_LOW_DEFAULT = 0.15
STOPWORDS_HIGH_DEFAULT = 0.20
NO_HEADINGS_DEFAULT = False
# Short and near-good headings within MAX_HEADING_DISTANCE characters before
# a good paragraph are classified as good unless --no-headings is specified.
MAX_HEADING_DISTANCE_DEFAULT = 200
PARAGRAPH_TAGS = frozenset({
    'body', 'blockquote', 'center', 'col', 'colgroup',
    'div', 'dl', 'fieldset', 'form', 'legend', 'optgroup',
    'p', 'pre', 'table', 'textarea', 'tfoot', 'thead', 'tr',
    'ul', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
})
# Cell/item-level tags. Research log 0009: the original jusText made each of these a
# separate paragraph, which fragmented table rows and lists into per-cell/per-item
# blocks the classifier then dropped piecemeal -- capping the oracle ceiling and
# wrecking row formatting (Levenshtein). We instead keep them INSIDE their containing
# row/list paragraph, separated by a space, so a <tr> becomes one row and a <ul> one
# block. This raised the general oracle F1 0.893->0.902 and Lev 0.822->0.838.
SEPARATOR_TAGS = frozenset({
    # <img> is a replaced inline element: an image BETWEEN two words (no surrounding
    # whitespace) mashed them together -- "Enhancing<img>Education" -> "EnhancingEducation"
    # (thejournal). Treat it like a cell separator so the words stay apart (research log 0083).
    'img',
    'td', 'th', 'li', 'dd', 'dt', 'option', 'caption',
})
_STRUCTURAL_LIST = ("nav", "menu", "tab", "crumb", "pag", "sidebar", "widget", "toolbar",
                    "social", "share", "related", "posts", "comment", "footer", "header",
                    "breadcrumb", "links")  # list classes that mark non-content lists (0049)

DEFAULT_ENCODING = 'utf8'
DEFAULT_ENC_ERRORS = 'replace'
# Sentinel for justext(model=...): the default auto-selects the best installed model (fastText
# stack -> bundled 3MB sklearn -> heuristic). Pass model=None to force the heuristic path.
AUTO_MODEL = object()
CHARSET_META_TAG_PATTERN = re.compile(br"""<meta[^>]+charset=["']?([^'"/>\s]+)""", re.IGNORECASE)
GOOD_OR_BAD = {'good', 'bad'}

# Mojibake repair (research log 0022). Some source pages arrive already mis-decoded
# (UTF-8 bytes read as Latin-1/CP1252, sometimes twice), so the input string contains
# garbage like ``â€™`` / ``Ã¢â‚¬â„¢`` instead of ``’``. jusText would faithfully emit the
# garbage. When ``fix_encoding`` is on we repair the input with ftfy -- but only when one
# of these tell-tale signatures is present, so clean documents are byte-for-byte untouched
# (no regression). Affects ~0.5% of general docs, 0% of the domain sets.
MOJIBAKE_PATTERN = re.compile("Ã[ƒ‚©¨¶°¢]|â€|â‚¬|Ã¢|Â[«»\xa0]")
_FTFY = None  # lazy ftfy module handle: None=unloaded, False=unavailable


def repair_mojibake(html_text):
    """Reverse double/single UTF-8<->CP1252 mojibake in *html_text* if detected.

    No-op when no mojibake signature is present, when the input is not a unicode
    string, or when ftfy is not installed (graceful degradation -- ftfy is an optional
    dependency). Tags are ASCII so they pass through untouched; only mis-decoded text is
    repaired.
    """
    global _FTFY
    if not isinstance(html_text, unicode) or not MOJIBAKE_PATTERN.search(html_text):
        return html_text
    if _FTFY is None:
        try:
            import ftfy
            _FTFY = ftfy
        except ImportError:
            _FTFY = False
    if not _FTFY:
        return html_text
    return _FTFY.fix_encoding(html_text)


# Angle-bracket emails (research log 0027). Usenet/old-forum quoting writes the author as
# ``"Joe" <joe@example.com> wrote:``. libxml2 treats ``<joe@example.com>`` as a bogus tag
# and DROPS it -- losing the address and mashing the surrounding text. Escaping these to
# ``&lt;...&gt;`` before parsing keeps them as text. The ``@`` before any space means it
# can never be a real tag (real tags have a space before attributes), so this won't touch
# ``<a href="mailto:x@y">``.
ANGLE_EMAIL_PATTERN = re.compile(r"<([a-zA-Z][^<>\s]*@[^<>\s]*)>")


def escape_angle_emails(html_text):
    """Escape ``<addr@host>`` so the parser keeps it as text instead of a bogus tag."""
    if not isinstance(html_text, unicode):
        return html_text
    return ANGLE_EMAIL_PATTERN.sub(r"&lt;\1&gt;", html_text)


# Double-encoded HTML entities (research log 0023). lxml decodes entities once while
# parsing; when the source was encoded twice (``&amp;amp;``) a literal ``&amp;`` survives
# into the output. A second unescape pass on the extracted text repairs it. Skipped for
# verbatim/code paragraphs, where an entity like ``&amp;`` may be shown intentionally.
ENTITY_PATTERN = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]{1,31});")


def decode_double_entities(paragraphs):
    """In-place: unescape surviving HTML entities in non-verbatim paragraph text."""
    for paragraph in paragraphs:
        if paragraph.verbatim:
            continue
        for i, node in enumerate(paragraph.text_nodes):
            if ENTITY_PATTERN.search(node):
                paragraph.text_nodes[i] = unescape(node)


# U+FFFD repair (research log 0029). A cp1252/Latin-1 byte decoded as utf-8 with
# errors='replace' becomes U+FFFD -- the byte is lost, but the surrounding context usually
# pins the original char (apostrophes in contractions dominate, then curly quotes, dashes,
# accents). _char_repair.REPAIR_TABLE maps a (2-before, 2-after) context to the most-likely
# char, learned high-confidence from train. Unknown contexts are left as U+FFFD (no guess).
_REPAIR_TABLE = None
_REPAIR_TABLE_1 = None


def repair_replacement_chars(paragraphs):
    """In-place: fill U+FFFD in non-verbatim paragraph text from the learned context tables.

    Tries the precise (2-before, 2-after) table first, then a (1-before, 1-after) fallback
    that recovers curly quotes / dashes the 2-char tier misses (research log 0036).
    """
    global _REPAIR_TABLE, _REPAIR_TABLE_1
    if _REPAIR_TABLE is None:
        from ._char_repair import REPAIR_TABLE, REPAIR_TABLE_1
        _REPAIR_TABLE = REPAIR_TABLE
        _REPAIR_TABLE_1 = REPAIR_TABLE_1
    if not _REPAIR_TABLE and not _REPAIR_TABLE_1:
        return
    for paragraph in paragraphs:
        if paragraph.verbatim:
            continue
        text = "".join(paragraph.text_nodes)
        if "�" not in text:
            continue
        chars = list(text)
        for i, ch in enumerate(chars):
            if ch == "�":
                repl = (_REPAIR_TABLE.get((text[i - 2:i], text[i + 1:i + 3]))
                        or _REPAIR_TABLE_1.get((text[i - 1:i], text[i + 1:i + 2])))
                if repl:
                    chars[i] = repl
        paragraph.text_nodes = ["".join(chars)]


# Orphaned list markers (research log 0053). A `<li>` whose text is preceded by a `<br>`
# (or a block child) gets the bullet/number marker and the item text split across a line
# break: after whitespace-normalization the merged list paragraph reads ``- \ntext`` →
# ``-\ntext``, orphaning the marker on its own line. The gold always joins ``- text`` on one
# line. This regex reattaches a marker that sits alone on a line to the content on the next
# line (289 occurrences across 46 dev docs). Matches only a line that is *exactly* a bullet
# (`-`) or an ordered marker (`12.`), followed by a newline then non-space content.
ORPHANED_MARKER_PATTERN = re.compile(r"(^|\n)(-|\d{1,3}\.)\n(?=\S)")
_BARE_MARKER = re.compile(r"^(-|\d{1,3}\.)$")


def fix_orphaned_list_markers(paragraphs):
    """In-place: rejoin a list marker orphaned from its item text.

    Two cases, both from a `<li>` whose text is preceded by a `<br>`/block:
    * within-paragraph -- the merged list paragraph reads ``…\n-\nitem…`` (marker on its own
      line); the regex reattaches it to the next line.
    * cross-paragraph -- the `<li>` wrapped a block, so the marker is its OWN paragraph and
      the item text is the next kept paragraph. Prepend the marker to that next kept
      paragraph and drop the marker paragraph. Only kept paragraphs are touched, so deduped
      content is never resurrected (cf. the 0052 peakbagger regression).
    """
    # Cross-paragraph: a kept <li> paragraph that is JUST a marker -> prepend to next kept.
    kept = [p for p in paragraphs if not p.is_boilerplate]
    for i, p in enumerate(kept[:-1]):
        text = p.text.strip()
        if (_BARE_MARKER.match(text) and "li" in p.dom_path.lower().split(".")):
            nxt = kept[i + 1]
            if _BARE_MARKER.match(nxt.text.strip()):
                continue  # don't merge a marker into another marker
            nxt.text_nodes = [text + " " + nxt.text]
            p.text_nodes = []
            p.class_type = "bad"

    # Within-paragraph: marker stranded on its own line inside a merged list paragraph.
    for paragraph in paragraphs:
        if paragraph.verbatim:
            continue
        text = paragraph.text
        if "\n" not in text:
            continue
        fixed = ORPHANED_MARKER_PATTERN.sub(r"\1\2 ", text)
        if fixed != text:
            paragraph.text_nodes = [fixed]


# Doubled list numbers (research log 0062). Some CMSs render a numbered list where each item
# *also* carries an explicit source number (recipe steps: `<li><span>2</span><span>In large
# bowl...`), so on top of our injected `<ol>` marker the paragraph reads ``2. 2 In large
# bowl``. We drop the redundant source number -- but only when the doubling is SYSTEMATIC
# (>=2 items whose source number equals the marker ordinal); a lone ``1. 1 cup flour`` is a
# real quantity and left untouched.
_DOUBLED_ORDINAL = re.compile(r"^(\d{1,3})\.\s+\1(?=\s|$)")
_BARE_ORDINAL = re.compile(r"^(\d{1,3})\.$")


def fix_doubled_list_numbers(paragraphs):
    """In-place: strip a source step-number that duplicates the injected ordinal marker."""
    kept = [p for p in paragraphs if not p.is_boilerplate]
    within = [p for p in kept if _DOUBLED_ORDINAL.match(p.text)]
    # Cross-paragraph: an inner block split the marker off, so a bare ``N.`` paragraph is
    # followed by a kept paragraph that starts with the same number ``N`` (the item text).
    orphans = []
    for i, p in enumerate(kept[:-1]):
        match = _BARE_ORDINAL.match(p.text.strip())
        if match and re.match(r"%s(?=\s)" % match.group(1), kept[i + 1].text.strip()):
            orphans.append((p, kept[i + 1], match.group(1)))
    if len(within) + len(orphans) < 2:
        return
    for paragraph in within:
        paragraph.text_nodes = [_DOUBLED_ORDINAL.sub(r"\1.", paragraph.text, count=1)]
    for marker_p, item_p, number in orphans:
        body = re.sub(r"^%s\s+" % number, "", item_p.text.strip())
        item_p.text_nodes = ["%s. %s" % (number, body)]
        marker_p.text_nodes = []
        marker_p.class_type = "bad"


# Unrendered MediaWiki markup (research log 0045). Some wiki pages (`index.php?title=...`
# source views) leak raw wikitext into the output -- `[[Link|text]]`, `{{templates}}`,
# `'''bold'''`, `== headings ==` -- which the gold renders to clean text. Strip the markup
# from a text node only when it clearly contains wiki links/templates (`[[`/`{{`), so prose
# with stray apostrophes is untouched. Skipped for verbatim/code paragraphs.
def _clean_wiki_node(node):
    for _ in range(3):
        node = re.sub(r"\{\{[^{}]*\}\}", "", node)              # {{templates}} (nested)
    node = re.sub(r"\[\[(?:[^\[\]|]*\|)?([^\[\]|]+)\]\]", r"\1", node)  # [[a|b]]->b, [[a]]->a
    node = re.sub(r"\[(?:https?|ftp)://\S+\s+([^\]]+)\]", r"\1", node)  # [url text]->text
    node = re.sub(r"'''''(.+?)'''''", r"\1", node)
    node = re.sub(r"'''(.+?)'''", r"\1", node)
    node = re.sub(r"''(.+?)''", r"\1", node)
    return re.sub(r"(?m)^\s*=+\s*(.+?)\s*=+\s*$", r"\1", node)   # == heading ==


def clean_wiki_markup(paragraphs):
    """In-place: strip unrendered MediaWiki markup from non-verbatim paragraph text."""
    for paragraph in paragraphs:
        if paragraph.verbatim:
            continue
        for i, node in enumerate(paragraph.text_nodes):
            if "[[" in node or "{{" in node:
                paragraph.text_nodes[i] = _clean_wiki_node(node)


class JustextError(Exception):
    "Base class for jusText exceptions."


class JustextInvalidOptions(JustextError):
    pass


def html_to_dom(html, default_encoding=DEFAULT_ENCODING, encoding=None, errors=DEFAULT_ENC_ERRORS):
    """Converts HTML to DOM."""
    if isinstance(html, unicode):
        decoded_html = html
        # encode HTML for case it's XML with encoding declaration
        forced_encoding = encoding if encoding else default_encoding
        html = html.encode(forced_encoding, errors)
    else:
        decoded_html = decode_html(html, default_encoding, encoding, errors)

    # Empty / whitespace-only input parses to "Document is empty" in lxml -- return an empty
    # document so justext() yields no paragraphs instead of raising.
    if not decoded_html or not decoded_html.strip():
        return lxml.html.fromstring("<html></html>")

    try:
        dom = lxml.html.fromstring(decoded_html, parser=lxml.html.HTMLParser())
    except ValueError:
        # Unicode strings with encoding declaration are not supported.
        # for XHTML files with encoding declaration, use the declared encoding
        dom = lxml.html.fromstring(html, parser=lxml.html.HTMLParser())
    except lxml.etree.ParserError:
        # Content with no parseable elements (e.g. only a comment or stray bytes).
        return lxml.html.fromstring("<html></html>")

    return dom


def decode_html(html, default_encoding=DEFAULT_ENCODING, encoding=None, errors=DEFAULT_ENC_ERRORS):
    """
    Converts a `html` containing an HTML page into Unicode.
    Tries to guess character encoding from meta tag.
    """
    if isinstance(html, unicode):
        return html

    if encoding:
        return html.decode(encoding, errors)

    match = CHARSET_META_TAG_PATTERN.search(html)
    if match:
        declared_encoding = match.group(1).decode("ASCII")
        # proceed unknown encoding as if it wasn't found at all
        with ignored(LookupError):
            return html.decode(declared_encoding, errors)

    # unknown encoding
    try:
        # try UTF-8 first
        return html.decode("utf8")
    except UnicodeDecodeError:
        # try lucky with default encoding
        try:
            return html.decode(default_encoding, errors)
        except UnicodeDecodeError as e:
            raise JustextError("Unable to decode the HTML to Unicode: " + unicode(e))


def preprocessor(dom):
    "Removes unwanted parts of DOM."
    options = {
        "processing_instructions": False,
        "remove_unknown_tags": False,
        "safe_attrs_only": False,
        "page_structure": False,
        "annoying_tags": False,
        "frames": False,
        "meta": False,
        "links": False,
        "javascript": False,
        "scripts": True,
        "comments": True,
        "style": True,
        "embedded": True,
        "forms": True,
        "kill_tags": ("head",),
    }
    cleaner = Cleaner(**options)

    return cleaner.clean_html(dom)


# Syntax-highlighter code tables (research log 0055). GitHub blob/gist and some highlighters
# (Crayon) render code as a <table>: one <tr> per line, a line-number "gutter" <td> plus a
# code <td>. jusText made each <tr> its own paragraph -- so the code came out with every line
# in a separate block (joined by a blank line) and its indentation stripped by whitespace
# normalization. We rewrite such a table into a single <pre> (verbatim) so the code keeps its
# indentation and reads as one block. Gated on an unambiguous line-number gutter (GitHub
# data-line-number / blob-num / crayon-num) so it never fires on a data table or a MediaWiki
# diff (those use lineno/de1/de2 -- deliberately excluded).
_CODE_GUTTER = re.compile(r"\b(?:blob-num|crayon-num)\b", re.I)


def _is_gutter_cell(td):
    return td.get("data-line-number") is not None or bool(_CODE_GUTTER.search(td.get("class") or ""))


def _code_block_text(el):
    "Serialize a code element to text: <br> -> newline, &nbsp; (U+00A0) -> space."
    for br in el.xpath(".//br"):
        # Strip newlines the source already put after the <br> (pretty-printed HTML) before
        # adding ours, so a "line<br>\nline" doesn't become a double blank line. Keep leading
        # spaces (= indentation) and a genuine <br><br> still yields a blank line.
        br.tail = "\n" + (br.tail or "").lstrip("\n\r")
    text = el.text_content().replace("\xa0", " ")
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n")


def rewrite_code_blocks(dom):
    """In-place: turn a multi-line ``<code>`` block into a verbatim ``<pre>``.

    Sites wrap a whole code listing in ``<code>`` (often inside a styled box), using ``<br>``
    for line breaks and ``&nbsp;`` for indentation (e.g. roseindia). jusText normalizes that
    away -- the code keeps its line breaks (``<br>`` -> newline, 0025) but loses indentation,
    because ``<code>`` is not verbatim. Converting a *block* ``<code>`` (multi-line, long) to a
    ``<pre>`` restores it. Gated to block code only (``<br>`` or newline AND >80 chars), so
    short inline ``<code>foo()</code>`` snippets in prose are untouched.
    """
    for code in dom.xpath("//code"):
        content = code.text_content() or ""
        if len(content) <= 80:
            continue
        # Require <br> line breaks: that marks a real multi-line code listing whose
        # indentation we lose. A <code> that relies only on source newlines is usually
        # pre-formatted already or a data blob (e.g. a JSON dump) the gold renders
        # differently -- converting it regresses (chroniclingamerica).
        if not code.xpath(".//br"):
            continue
        text = _code_block_text(code)
        if not text:
            continue
        pre = code.makeelement("pre")
        pre.text = text
        parent = code.getparent()
        if parent is not None:
            parent.replace(code, pre)
    return dom


def rewrite_code_tables(dom):
    "In-place: replace line-numbered syntax-highlighter code tables with a single <pre>."
    for table in dom.xpath("//table"):
        if sum(1 for td in table.xpath(".//td") if _is_gutter_cell(td)) < 4:
            continue
        lines = []
        for tr in table.xpath(".//tr"):
            cells = tr.xpath("./td")
            code = [td for td in cells if not _is_gutter_cell(td)]
            lines.append(code[-1].text_content() if code else "")
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip("\n")
        if not text:
            continue
        pre = table.makeelement("pre")
        pre.text = text
        parent = table.getparent()
        if parent is not None:
            parent.replace(table, pre)
    return dom


# super(...).__init__() breaks Python 2.7 - TypeError: super() argument 1 must be type, not classobj
# noinspection PyMissingConstructor
class ParagraphMaker(ContentHandler):
    """
    A class for converting a HTML page represented as a DOM object into a list
    of paragraphs.
    """

    @classmethod
    def make_paragraphs(cls, root):
        """Converts DOM into paragraphs."""
        handler = cls()
        lxml.sax.saxify(root, handler)
        return handler.paragraphs

    def __init__(self):
        self.path = PathInfo()
        self.paragraphs = []
        self.paragraph = None
        self.link = False
        self.br = False
        self.pre = 0  # depth inside <pre>/<textarea>: preserve whitespace verbatim (0021)
        self.skip = 0  # depth inside <style>/<script>: their text is never content (0064)
        self.list_stack = []  # stack of [tag, counter] for <ol>/<ul> list markers (0037)
        self._start_new_pragraph()

    def _start_new_pragraph(self):
        if self.paragraph and self.paragraph.contains_text():
            self.paragraphs.append(self.paragraph)

        self.paragraph = Paragraph(self.path)

    def startElementNS(self, name, qname, attrs):
        name = name[1]
        self.path.append(name)

        # <style>/<script> text is never content. The non-forum path strips them in the
        # preprocessor, but forum handlers run ParagraphMaker on the raw post body, where an
        # inline `<style>img.top{...}</style>` before a math <img> would otherwise leak its
        # CSS as text (mathhelpforum equations -> "img.top {vertical-align:15%;}"); 0064.
        if name in ("style", "script"):
            self.skip += 1

        # Track list nesting so <li> items get markdown markers (research log 0037).
        # Skip markers for STRUCTURAL lists (forum post lists, nav/menus/sidebars) whose
        # class flags them as non-content -- otherwise forum posts in `<ol class="posts">`
        # get numbered "1. 2." when a forum handler misses the page (research log 0049).
        if name in ("ol", "ul"):
            try:
                cls = (attrs.get((None, "class")) or "").lower()
            except Exception:
                cls = ""
            emit = not any(k in cls for k in _STRUCTURAL_LIST)
            self.list_stack.append([name, 0, emit])

        if name in PARAGRAPH_TAGS or (name == "br" and self.br):
            if name == "br":
                # the <br><br> is a paragraph separator and should
                # not be included in the number of tags within the
                # paragraph
                self.paragraph.tags_count -= 1
            self._start_new_pragraph()
            # <pre>/<textarea> content is verbatim: keep indentation & line breaks (0021)
            if name in ("pre", "textarea"):
                self.pre += 1
                self.paragraph.verbatim = True
        else:
            # Cell/item tags don't break the paragraph (0009) but separate their
            # text with a space so a row reads "Bedrooms: 4", not "Bedrooms4".
            if name in SEPARATOR_TAGS:
                # A list item starts a new line with its marker -- "1. " inside <ol>,
                # "- " inside <ul> -- so numbered/bulleted lists keep their structure
                # (research log 0037). normalize_whitespace keeps the leading \n.
                if name == "li" and self.list_stack and self.list_stack[-1][2]:
                    item = self.list_stack[-1]
                    item[1] += 1
                    marker = ("%d. " % item[1]) if item[0] == "ol" else "- "
                    self.paragraph.append_text("\n" + marker)
                else:
                    self.paragraph.append_text(' ')
            self.br = bool(name == "br")
            if self.br:
                # A single <br> is a line break: emit a newline (the gold respects
                # <br> line structure -- addresses, contact blocks, <br>-separated
                # lists/publications). normalize_whitespace keeps the \n because the
                # run contains a newline (research log 0025). <br><br> still becomes a
                # paragraph break via the name=="br" and self.br branch above.
                self.paragraph.append_text('\n')
            elif name == 'address':
                # <address> is block-level; adjacent contact blocks (officer lists, etc.)
                # were glued -- "Treasurer</address><address>Julia" -> "TreasurerJulia"
                # (pajcisenate). The gold puts each on its own line, so emit a newline like
                # <br> -- a line break within the block, not a paragraph split that would let
                # the classifier drop rows piecemeal (research log 0083).
                self.paragraph.append_text('\n')
            elif name == 'a':
                self.link = True
            self.paragraph.tags_count += 1

    def endElementNS(self, name, qname):
        name = name[1]
        self.path.pop()

        if name in ("pre", "textarea") and self.pre > 0:
            self.pre -= 1
        if name in ("style", "script") and self.skip > 0:
            self.skip -= 1
        if name in ("ol", "ul") and self.list_stack:
            self.list_stack.pop()
        if name in PARAGRAPH_TAGS:
            self._start_new_pragraph()
        elif name in SEPARATOR_TAGS:
            self.paragraph.append_text(' ')
        if name == 'a':
            self.link = False

    def endDocument(self):
        self._start_new_pragraph()

    def characters(self, content):
        # <style>/<script> CSS/JS text is never document content (research log 0064).
        if self.skip > 0:
            return
        # Inside <pre>/<textarea> keep whitespace verbatim (don't skip blank, don't
        # normalize) so code indentation and line breaks survive (research log 0021).
        if self.pre > 0:
            self.paragraph.verbatim = True
            text = self.paragraph.append_text(content, normalize=False)
        else:
            if is_blank(content):
                # Whitespace between inline elements -- e.g. "<a>data</a> <a>x</a>" or
                # word-per-span CMS markup -- arrives as a blank text node. Dropping it
                # mashed adjacent words ("datatransmission"); keep a single space so they
                # stay separated (research log 0026). normalize_whitespace collapses any
                # resulting run, so this can never double-space; the guard avoids a
                # leading space on a fresh paragraph. self.br is left untouched so a
                # "<br> <br>" still resolves to a paragraph break.
                if self.paragraph.text_nodes:
                    self.paragraph.append_text(' ')
                return
            # Newlines inside a source text node are just HTML pretty-printing (indented
            # `<dt>`/`<dd>`/`<td>` cells, wrapped prose) -- collapse them to spaces so a
            # quantity and its ingredient read "1 1/2 lb beef", not split across two lines.
            # Real line breaks come from `<br>`/list markers, which inject their own '\n'
            # via the element handlers, so those survive (research log 0061).
            text = self.paragraph.append_text(content.replace("\r", " ").replace("\n", " "))

        if self.link:
            self.paragraph.chars_count_in_links += len(text)
        self.br = False


class PathInfo(object):
    def __init__(self):
        # list of triples (tag name, order, children)
        self._elements = []

    @property
    def dom(self):
        return ".".join(e[0] for e in self._elements)

    @property
    def xpath(self):
        return "/" + "/".join("%s[%d]" % e[:2] for e in self._elements)

    def append(self, tag_name):
        children = self._get_children()
        order = children.get(tag_name, 0) + 1
        children[tag_name] = order

        xpath_part = (tag_name, order, {})
        self._elements.append(xpath_part)

        return self

    def _get_children(self):
        if not self._elements:
            return {}

        return self._elements[-1][2]

    def pop(self):
        self._elements.pop()
        return self


@lru_cache(maxsize=128)  # 100 stoplists
def define_stoplist(stoplist):
    "Lower-case all words in stoplist and create frozen set."
    stoplist = frozenset(w.lower() for w in stoplist)
    return stoplist


def classify_paragraphs(paragraphs, stoplist, length_low=LENGTH_LOW_DEFAULT,
        length_high=LENGTH_HIGH_DEFAULT, stopwords_low=STOPWORDS_LOW_DEFAULT,
        stopwords_high=STOPWORDS_HIGH_DEFAULT, max_link_density=MAX_LINK_DENSITY_DEFAULT,
        no_headings=NO_HEADINGS_DEFAULT):
    "Context-free paragraph classification."

    stoplist = define_stoplist(stoplist)
    for paragraph in paragraphs:
        length = len(paragraph)
        stopword_density = paragraph.stopwords_density(stoplist)
        link_density = paragraph.links_density()
        paragraph.heading = bool(not no_headings and paragraph.is_heading)

        if link_density > max_link_density:
            paragraph.cf_class = 'bad'
        elif ('\xa9' in paragraph.text) or ('&copy' in paragraph.text):
            paragraph.cf_class = 'bad'
        elif 'select' in paragraph.dom_path:
            paragraph.cf_class = 'bad'
        elif length < length_low:
            if paragraph.chars_count_in_links > 0:
                paragraph.cf_class = 'bad'
            else:
                paragraph.cf_class = 'short'
        elif stopword_density >= stopwords_high:
            if length > length_high:
                paragraph.cf_class = 'good'
            else:
                paragraph.cf_class = 'neargood'
        elif stopword_density >= stopwords_low:
            paragraph.cf_class = 'neargood'
        else:
            paragraph.cf_class = 'bad'


def _get_neighbour(i, paragraphs, ignore_neargood, inc, boundary):
    while i + inc != boundary:
        i += inc
        c = paragraphs[i].class_type
        if c in GOOD_OR_BAD:
            return c
        if c == 'neargood' and not ignore_neargood:
            return c
    return 'bad'


def get_prev_neighbour(i, paragraphs, ignore_neargood):
    """
    Return the class of the paragraph at the top end of the short/neargood
    paragraphs block. If ignore_neargood is True, than only 'bad' or 'good'
    can be returned, otherwise 'neargood' can be returned, too.
    """
    return _get_neighbour(i, paragraphs, ignore_neargood, -1, -1)


def get_next_neighbour(i, paragraphs, ignore_neargood):
    """
    Return the class of the paragraph at the bottom end of the short/neargood
    paragraphs block. If ignore_neargood is True, than only 'bad' or 'good'
    can be returned, otherwise 'neargood' can be returned, too.
    """
    return _get_neighbour(i, paragraphs, ignore_neargood, 1, len(paragraphs))


def revise_paragraph_classification(paragraphs, max_heading_distance=MAX_HEADING_DISTANCE_DEFAULT):
    """
    Context-sensitive paragraph classification. Assumes that classify_pragraphs
    has already been called.
    """

    # good headings
    for i, paragraph in enumerate(paragraphs):
        # copy classes
        paragraph.class_type = paragraph.cf_class
        if not (paragraph.heading and paragraph.class_type == 'short'):
            continue
        j = i + 1
        distance = 0
        while j < len(paragraphs) and distance <= max_heading_distance:
            if paragraphs[j].class_type == 'good':
                paragraph.class_type = 'neargood'
                break
            distance += len(paragraphs[j].text)
            j += 1

    # classify short
    new_classes = {}
    for i, paragraph in enumerate(paragraphs):
        if paragraph.class_type != 'short':
            continue
        prev_neighbour = get_prev_neighbour(i, paragraphs, ignore_neargood=True)
        next_neighbour = get_next_neighbour(i, paragraphs, ignore_neargood=True)
        if prev_neighbour == 'good' and next_neighbour == 'good':
            new_classes[i] = 'good'
        elif prev_neighbour == 'bad' and next_neighbour == 'bad':
            new_classes[i] = 'bad'
        # it must be set(['good', 'bad'])
        elif (prev_neighbour == 'bad' and get_prev_neighbour(i, paragraphs, ignore_neargood=False) == 'neargood') or \
             (next_neighbour == 'bad' and get_next_neighbour(i, paragraphs, ignore_neargood=False) == 'neargood'):
            new_classes[i] = 'good'
        else:
            new_classes[i] = 'bad'

    for i, c in new_classes.items():
        paragraphs[i].class_type = c

    # revise neargood
    for i, paragraph in enumerate(paragraphs):
        if paragraph.class_type != 'neargood':
            continue
        prev_neighbour = get_prev_neighbour(i, paragraphs, ignore_neargood=True)
        next_neighbour = get_next_neighbour(i, paragraphs, ignore_neargood=True)
        if (prev_neighbour, next_neighbour) == ('bad', 'bad'):
            paragraph.class_type = 'bad'
        else:
            paragraph.class_type = 'good'

    # more good headings
    for i, paragraph in enumerate(paragraphs):
        if not (paragraph.heading and paragraph.class_type == 'bad' and paragraph.cf_class != 'bad'):
            continue
        j = i + 1
        distance = 0
        while j < len(paragraphs) and distance <= max_heading_distance:
            if paragraphs[j].class_type == 'good':
                paragraph.class_type = 'good'
                break
            distance += len(paragraphs[j].text)
            j += 1


# Q&A role transform (research log 0031). StackExchange-engine pages (stackoverflow,
# superuser, *.stackexchange.com, ...) are detected by their DOM signature and rewritten so
# each post's role + author appears BEFORE its body -- "**Question (user)**", "**Answer
# (user)**" -- in post order, matching the gold. This is the main transformation the gold
# applies to forum content. Bodies are run back through ParagraphMaker so they inherit the
# code-verbatim / <br> / list handling. Comments are excluded (the gold mostly omits them).
def _qa_author(post):
    """Best-effort post author: the owner signature, else the last user-details link."""
    for xpath in ('.//*[contains(@class,"owner")]//*[contains(@class,"user-details")]//a',
                  './/*[contains(@class,"user-details")]//a'):
        links = post.xpath(xpath)
        if links:
            name = links[-1].text_content().strip()
            if name:
                return name
    return None


def _marker_paragraph(text):
    """A synthetic kept paragraph carrying a literal role marker / title."""
    paragraph = Paragraph(PathInfo())
    paragraph.append_text(text)
    paragraph.class_type = "good"
    return paragraph


def _qa_comments(post):
    """(author, text) for each comment on a post, in document order, de-duplicated.

    Comments are kept as one contiguous thread per post (never a scattered subset): a
    later comment often builds on earlier ones, so dropping middle comments would break the
    thread (user guidance, research log 0034).
    """
    out, seen = [], set()
    for comment in post.xpath('.//*[contains(@class,"comment-copy")]'):
        text = comment.text_content().strip()
        key = re.sub(r"\s+", " ", text)
        if len(text) <= 1 or key in seen:
            continue
        seen.add(key)
        author = comment.getparent().xpath('.//*[contains(@class,"comment-user")]//text()')
        out.append((author[0].strip() if author else None, text))
    return out


def stackexchange_paragraphs(dom, include_comments=True):
    """Return role-prefixed Q&A paragraphs for a StackExchange page, or None if not one.

    Comments are INCLUDED by default as the full contiguous thread per post (research log
    0034). The gold includes comments inconsistently (~50% of pages) with NO learnable
    signal -- score, length, and displayed-vs-hidden all fail to separate kept from dropped
    -- so matching the gold is impossible. Comments are real content (corrections, the
    answer-in-a-comment), so the uniform principled policy is to keep the whole thread,
    never a scattered subset (a later comment builds on earlier ones). Costs ~0.001 F1 on
    general/dev. ``include_comments=False`` opts out for strict gold-matching benchmarking.
    """
    questions = dom.xpath('//div[@id="question"]')
    if not questions:
        return None
    paragraphs = []
    title = dom.xpath('//*[contains(@class,"question-hyperlink")]//text()')
    if not title:
        title = dom.xpath('//h1//text()')
    if title:
        paragraphs.append(_marker_paragraph(title[0].strip()))
    answers = dom.xpath('//div[starts-with(@id,"answer-")]')
    # The accepted answer is flagged only on multi-answer threads, where naming the canonical
    # solution carries signal -- with a single answer there is nothing to contrast, and the
    # gold omits the flag there 16/19 of the time (research log 0059). The gold applies
    # "(accepted)" inconsistently on multi-answer threads (~50%, no learnable pattern), so this
    # is a deliberate quality signal at ~zero full-dataset metric cost, not a gold-match.
    multi = len(answers) > 1
    posts = [("Question", questions[0], False)]
    posts += [("Answer", a, multi and "accepted-answer" in (a.get("class") or ""))
              for a in answers]
    for role, post, accepted in posts:
        author = _qa_author(post)
        marker = "**%s (%s)**" % (role, author) if author else "**%s**" % role
        if accepted:
            marker += " (accepted)"
        paragraphs.append(_marker_paragraph(marker))
        bodies = post.xpath('.//*[contains(@class,"post-text") or @itemprop="text"]')
        if bodies:
            for body in ParagraphMaker.make_paragraphs(bodies[0]):
                if body.text.strip():
                    body.class_type = "good"
                    paragraphs.append(body)
        if include_comments:
            comments = _qa_comments(post)
            if comments:
                lines = "\n".join(
                    ("- **%s:** %s" % (a, t) if a else "- " + t) for a, t in comments)
                paragraphs.append(_marker_paragraph("**Comments**\n" + lines))
    return paragraphs


def _strip_quote_blocks(element):
    """Deep-copy *element* with vBulletin/bbcode quote blocks removed (keeps code).

    Excludes ``blockquote.postcontent`` -- vBulletin 4 wraps the *whole post body* in
    ``<blockquote class="postcontent restore">``, so stripping every blockquote deleted the
    entire post and the handler silently fell through to the model (research log 0063). Real
    reply-quotes (bbcode ``.quote``/``.bbcode_quote``, phpBB ``<blockquote>``) are still
    removed.
    """
    element = copy.deepcopy(element)
    for quote in element.xpath(
            './/*[contains(@class,"quote")] | .//blockquote[not(contains(@class,"postcontent"))]'):
        parent = quote.getparent()
        if parent is not None:
            parent.remove(quote)
    return element


def _post_container(body, others):
    """Largest ancestor of *body* that contains none of the *others* post bodies.

    Scopes a post to its own block across vBulletin skins, so the author/date are read from
    THIS post's header -- not a high shared ancestor's first user (research log 0039, which
    fixed the 0038 misattribution bug).
    """
    container = body
    while container.getparent() is not None:
        parent = container.getparent()
        if any(parent in o.iterancestors() for o in others):
            return container
        container = parent
    return container


def _clean_forum_date(text):
    """Tidy a raw forum date string toward the gold's form (drop ordinals/trailing comma)."""
    return re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", re.sub(r"\s+", " ", text)).strip().strip(",")


def _forum_thread_paragraphs(dom, posts):
    """Assemble role-prefixed paragraphs from forum *posts* = [(username, date, body_paras)].

    Shared by the per-engine forum handlers (research log 0039/0040): title, then per post a
    ``**username** (date)`` marker followed by its body. Returns None if <2 posts.
    """
    if len(posts) < 2:
        return None
    paragraphs = []
    title = dom.xpath('//h1//text()') or dom.xpath('//h2//text()')
    if title and title[0].strip():
        paragraphs.append(_marker_paragraph(title[0].strip()))
    for username, date, body_paras in posts:
        marker = "**%s** (%s)" % (username, date) if date else "**%s**" % username
        paragraphs.append(_marker_paragraph(marker))
        for body in body_paras:
            body.class_type = "good"
            paragraphs.append(body)
    return paragraphs


def vbulletin_paragraphs(dom, include_comments=True):
    """Role-prefixed paragraphs for a vBulletin forum thread, or None if not one.

    Brings each poster's name + date to the front -- `**username** (date)` -- in post order
    (research log 0039). Per-post author/date are read from the post's own block
    (`_post_container`, the largest ancestor with no other post body, which fixes the 0038
    misattribution); embedded "Originally Posted by..." quote blocks are stripped. Fires only
    when >=2 posts have a username (else falls back to the normal path).
    """
    bodies = dom.xpath('//*[starts-with(@id,"post_message_")]')
    if len(bodies) < 2:
        return None
    posts = []
    for body_el in bodies:
        others = [b for b in bodies if b is not body_el]
        container = _post_container(body_el, others)
        # First *non-empty* username: some skins (androidcentral) put an empty avatar <a
        # class="username"> before the text one, so users[0] is blank and would skip the post.
        users = container.xpath('.//a[contains(@class,"username")]')
        username = next((u.text_content().strip() for u in users
                         if u.text_content().strip()), "")
        if not username:
            continue
        dates = container.xpath('.//*[contains(@class,"date")]//text()')
        date = _clean_forum_date(" ".join(d.strip() for d in dates if d.strip()))
        body_paras = [p for p in ParagraphMaker.make_paragraphs(_strip_quote_blocks(body_el))
                      if p.text.strip()]
        if body_paras:
            posts.append((username, date, body_paras))
    return _forum_thread_paragraphs(dom, posts)


# Fallback forum-date for phpBB skins that don't use the "by X on DATE" wording -- e.g. the
# WP-integrated theme whose byline is "Wed Oct 15, 2008 10:52 am by don" (date *before* the
# author). Matches "Mon DD, YYYY [HH:MM am]" with an optional leading weekday (research log 0072).
_PHPBB_DATE = re.compile(
    r"(?:[A-Z][a-z]{2}\s+)?[A-Z][a-z]{2,8}\s+\d{1,2},?\s+\d{4}(?:\s+\d{1,2}:\d{2}\s*[ap]m)?", re.I)
# Non-author link labels in a phpBB `.author` line (post-icon, action links).
_PHPBB_NONAUTHOR = re.compile(r"^(?:post|reply|quote|edit|report|top|profile|pm|email|www)$", re.I)


def phpbb_paragraphs(dom, include_comments=True):
    """Role-prefixed paragraphs for a phpBB forum thread, or None if not one.

    phpBB's `.postbody` holds both the author line ("by <name> on <date>") and the post
    `.content`; reuses the shared assembler + quote-stripping (research log 0040). Fires only
    when >=2 posts have an author + content (else falls back).
    """
    postbodies = dom.xpath('//*[contains(@class,"postbody")]')
    if len(postbodies) < 2:
        return None
    posts = []
    for postbody in postbodies:
        authors = postbody.xpath('.//*[contains(@class,"author")]')
        username = ""
        if authors:
            # Newer phpBB skins put a post-icon link ("Post", wrapping an imageset/icon span)
            # BEFORE the real author link, so links[0] was wrongly used as the name (every post
            # titled "Post" -- research log 0080). Skip icon links and generic-label links; the
            # author is the first remaining link, or the "by <name> »" text as a fallback.
            for a in authors[0].xpath('.//a'):
                if a.xpath('.//*[contains(@class,"imageset") or contains(@class,"icon")]'):
                    continue
                text = a.text_content().strip()
                if text and not _PHPBB_NONAUTHOR.match(text):
                    username = text
                    break
            if not username:
                match = re.search(r"\bby\s+(.+?)\s*»",
                                  re.sub(r"\s+", " ", authors[0].text_content()))
                if match:
                    username = match.group(1).strip()
        content = postbody.xpath('.//*[contains(@class,"content")]')
        if not username or not content:
            continue
        date = ""
        if authors:
            text = re.sub(r"\s+", " ", authors[0].text_content()).strip()
            match = re.search(r"(?:\bon\b|»)\s+(.+)$", text)
            if match:
                date = _clean_forum_date(match.group(1))
            else:                                  # "DATE by author" skins (research log 0072)
                match = _PHPBB_DATE.search(text)
                if match:
                    date = _clean_forum_date(match.group())
        body_el = _strip_quote_blocks(content[0])
        # Some skins wrap the byline + per-post subject heading *inside* `.content`; strip them
        # so they don't leak into the body. No-op on standard phpBB3 / punbb where the body is
        # the whole `.content` (research log 0072).
        for meta in body_el.xpath(
                './/*[contains(@class,"author")]'
                ' | .//h3[contains(concat(" ", @class, " "), " first ")]'):
            parent = meta.getparent()
            if parent is not None:
                parent.remove(meta)
        body_paras = [p for p in ParagraphMaker.make_paragraphs(body_el) if p.text.strip()]
        if body_paras:
            posts.append((username, date, body_paras))
    return _forum_thread_paragraphs(dom, posts)


def bbpress_paragraphs(dom, include_comments=True):
    """Role-prefixed paragraphs for a bbPress (WordPress) forum thread, or None.

    bbPress has clean per-post selectors: body `.bbp-reply-content`/`.bbp-topic-content`,
    author in the post's `.bbp-author-name` (research log 0048). Reuses the shared assembler
    + quote-strip. Fires only with >=2 posts that have an author.
    """
    bodies = dom.xpath('//*[contains(@class,"bbp-reply-content") or contains(@class,"bbp-topic-content")]')
    if len(bodies) < 2:
        return None
    posts = []
    for body in bodies:
        author, ancestor = "", body
        for _ in range(6):
            ancestor = ancestor.getparent()
            if ancestor is None:
                break
            names = ancestor.xpath('.//*[contains(@class,"bbp-author-name")]//text()')
            if names:
                author = names[0].strip()
                break
        if not author:
            continue
        body_paras = [p for p in ParagraphMaker.make_paragraphs(_strip_quote_blocks(body))
                      if p.text.strip()]
        if body_paras:
            posts.append((author, "", body_paras))
    return _forum_thread_paragraphs(dom, posts)


_SMF_DATE = re.compile(r"[A-Z][a-z]{2}\w*\s+\d{1,2},?\s+\d{4},?\s+\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)")


def smf_paragraphs(dom, include_comments=True):
    """Role-prefixed paragraphs for an SMF (Simple Machines) forum thread, or None.

    SMF posts are `div.post` (body in a nested `.inner` message div) paired with a sibling
    `.poster` block; the post date sits in a header `.smalltext` (research log 0046). Body is
    `.inner` (drops the signature/"Logged" chrome that wraps it); quotes are KEPT (SMF gold
    keeps them). Author/date scoped to the post's own block via `_post_container`. Fires only
    with >=2 posts that have a username.
    """
    bodies = dom.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " post ")]')
    if len(bodies) < 2:
        return None
    posts = []
    for body in bodies:
        others = [b for b in bodies if b is not body]
        block = _post_container(body, others)
        posters = block.xpath('.//*[contains(@class,"poster")]')
        if not posters:
            continue
        names = posters[0].xpath('.//h4//text()|.//a//text()')
        username = next((t.strip() for t in names if t.strip()), "")
        if not username:
            continue
        inner = body.xpath('.//*[contains(@class,"inner")]')
        body_el = inner[0] if inner else body
        body_descendants = set(body_el.iter())
        date = ""
        for small in block.xpath('.//*[contains(@class,"smalltext")]'):
            if small in body_descendants:
                continue
            match = _SMF_DATE.search(small.text_content())
            if match:
                date = _clean_forum_date(match.group())
                break
        body_paras = [p for p in ParagraphMaker.make_paragraphs(body_el) if p.text.strip()]
        if body_paras:
            posts.append((username, date, body_paras))
    return _forum_thread_paragraphs(dom, posts)


# XenForo's full date+time lives in the DateTime element's ``title`` ("Dec 31, 2009 at
# 7:49 AM"); the visible text is only the day. We pull the title and drop the " at " so the
# marker carries the time the gold keeps.
_XENFORO_DATE = re.compile(
    r"[A-Z][a-z]{2}\w*\s+\d{1,2},?\s+\d{4}(?:,?\s+\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))?")


def xenforo_paragraphs(dom, include_comments=True):
    """Role-prefixed paragraphs for a XenForo forum thread, or None if not one.

    XenForo posts are ``blockquote.messageText`` bodies; the author is the post block's
    ``data-author`` (falling back to the ``.messageUserBlock`` username link) and the
    date+time is in a ``.DateTime`` element's ``title`` attribute (research log 0058).
    Reuses the shared assembler + quote-strip: the gold drops reply-quotes (keeping them
    regresses train by 1.6 F1), so quotes are stripped even though one doc that pastes its
    own logs into a quote loses that content -- a quote-keep policy can't tell the two apart
    (the lost content isn't concentrated in a single quote) and costs far more than it saves.
    Author/date scoped to the post's own block via ``_post_container``. Fires only with >=2
    posts that have an author.
    """
    bodies = dom.xpath('//blockquote[contains(concat(" ", @class, " "), " messageText ")]')
    if len(bodies) < 2:
        return None
    posts = []
    for body in bodies:
        others = [b for b in bodies if b is not body]
        block = _post_container(body, others)
        author, anc = "", block
        for _ in range(6):
            if anc is None:
                break
            if anc.get("data-author"):
                author = anc.get("data-author").strip()
                break
            anc = anc.getparent()
        if not author:
            names = block.xpath('.//*[contains(@class,"messageUserBlock")]//a//text()')
            author = next((t.strip() for t in names if t.strip()), "")
        if not author:
            continue
        date = ""
        for dt in block.xpath('.//*[contains(@class,"DateTime")]'):
            raw = re.sub(r"\s+at\s+", " ",
                         re.sub(r"\s+", " ", dt.get("title") or dt.text_content()))
            match = _XENFORO_DATE.search(raw.strip())
            if match:
                date = _clean_forum_date(match.group())
                break
        body_paras = [p for p in ParagraphMaker.make_paragraphs(_strip_quote_blocks(body))
                      if p.text.strip()]
        if body_paras:
            posts.append((author, date, body_paras))
    return _forum_thread_paragraphs(dom, posts)


_JFORUM_DATE = re.compile(r"[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?")


def jforum_paragraphs(dom, include_comments=True):
    """Role-prefixed paragraphs for a JForum thread (coderanch), or None (research log 0077).

    JForum lays each post out as an author block (``.authorName``/``.authorNameNoLink``) and a
    ``td.postbody`` in separate rows of one table; they're paired by document order. The date
    is in a nearby ``.postdetails``. Fires only with >=2 posts where authors and bodies match
    one-to-one (else falls back)."""
    bodies = dom.xpath('//td[contains(@class, "postbody")]')
    authors = dom.xpath('//*[contains(@class, "authorName")]')
    if len(bodies) < 2 or len(authors) != len(bodies):
        return None
    posts = []
    for author_el, body in zip(authors, bodies):
        name = re.sub(r"\s+", " ", author_el.text_content()).strip()
        if not name:
            continue
        date, anc = "", author_el
        for _ in range(4):
            anc = anc.getparent()
            if anc is None:
                break
            for t in anc.xpath('.//*[contains(@class,"postdetails")]//text()'):
                match = _JFORUM_DATE.search(t)
                if match:
                    date = _clean_forum_date(match.group())
                    break
            if date:
                break
        body_paras = [p for p in ParagraphMaker.make_paragraphs(_strip_quote_blocks(body))
                      if p.text.strip()]
        if body_paras:
            posts.append((name, date, body_paras))
    return _forum_thread_paragraphs(dom, posts)


_POSTED_BY = re.compile(r"Posted by\s+(.+?)\s+on\s+(.+)", re.I)


def workitmom_paragraphs(dom, include_comments=True):
    """Role-prefixed paragraphs for a Drupal-style group/forum thread, or None (research log
    0071). Posts are ``li[id^=post_]``; the body is ``div.body`` and the author + date come
    from a ``.comment-by`` line of the form "Posted by <name> on <date>". Fires only with >=2
    such posts (else falls back to the normal path)."""
    posts_li = dom.xpath('//li[starts-with(@id, "post_")][.//*[contains(@class, "comment-by")]]')
    if len(posts_li) < 2:
        return None
    posts = []
    for li in posts_li:
        cb = li.xpath('.//*[contains(@class, "comment-by")]')
        if not cb:
            continue
        match = _POSTED_BY.search(re.sub(r"\s+", " ", cb[0].text_content()).strip())
        if not match:
            continue
        author, date = match.group(1).strip(), _clean_forum_date(match.group(2))
        body = li.xpath('.//div[contains(concat(" ", @class, " "), " body ")]')
        if not body:
            continue
        body_paras = [p for p in ParagraphMaker.make_paragraphs(body[0]) if p.text.strip()]
        if body_paras:
            posts.append((author, date, body_paras))
    return _forum_thread_paragraphs(dom, posts)


# DSpace repository item-view metadata (research log 0082). The label/value rows live in a
# ``table.itemDisplayTable``. Most skins render label+value as one block the classifier keeps
# (lirias.kuleuven, econstor -- already ~0.99); a few split them into separate cells, so the
# link-dense author value is dropped, leaving a bare "Authors" label (hub.hku.hk 0.87).
_DSPACE_BARE_LABEL = re.compile(
    r"^(Authors?|Title|Citation|Issue Date|Abstract|Keywords?|Publisher"
    r"|Persistent Identifier)$")


def _dspace_metadata(dom):
    """DSpace item metadata as gold-style lines (Title -> heading, authors joined with '; ',
    every other row -> 'Label: value'), or None if the page has no ``itemDisplayTable``.

    Read from the raw DOM before preprocessing (links must survive). Only *applied* when the
    base extraction shows the split-cell failure -- see the gate in ``justext`` -- so the
    skins the classifier already handles well are left untouched.
    """
    tables = dom.xpath('//table[contains(@class, "itemDisplayTable")]')
    if not tables:
        return None
    lines = []
    for row in tables[0].xpath('./tr | ./tbody/tr'):
        cells = row.xpath('./td | ./th')
        if len(cells) < 2:
            continue
        label = " ".join(cells[0].text_content().split()).rstrip(":").strip()
        value_cell = cells[-1]
        links = value_cell.xpath('.//a')
        if label.lower() in ("author", "authors") and len(links) >= 2:
            value = "; ".join(" ".join(a.text_content().split()) for a in links
                              if a.text_content().strip())
        else:
            value = " ".join(value_cell.text_content().split())
        if not label or not value:
            continue
        lines.append(value if label.lower() == "title" else "%s: %s" % (label, value))
    for holder in dom.xpath('//*[strong[contains(text(), "Appears in Collections")]]'):
        cols = [" ".join(a.text_content().split()) for a in holder.xpath('.//a')]
        if cols:
            lines.append("Appears in Collections: " + "; ".join(cols))
        break
    return lines or None


def _has_bare_dspace_label(paragraphs):
    """True if a kept paragraph is exactly a DSpace metadata label with no value -- the
    split-cell failure where the value (e.g. link-dense authors) was dropped."""
    return any(not p.is_boilerplate and _DSPACE_BARE_LABEL.match(p.text.strip())
               for p in paragraphs)


def _table_xpath_key(xpath):
    """Return the xpath prefix up to and including the innermost ``table[N]`` segment,
    or None if the path is not inside a table. Used to group sibling table rows."""
    segs = xpath.split("/")
    last_table = None
    for i, s in enumerate(segs):
        if s.startswith("table["):
            last_table = i
    return "/".join(segs[: last_table + 1]) if last_table is not None else None


def merge_uniform_table_rows(paragraphs, min_rows=8, min_kept=2, max_link_density=0.6,
        max_cv=0.4, max_median_len=160):
    """Keep ALL rows of a *uniform data table* when the classifier kept some but dropped
    others -- those drops are near-certainly noise.

    A learned/heuristic classifier scores each table row independently, so on a long
    standings/stats/spec table (rows that are short and near-identical) it keeps a few rows
    and drops structurally-identical siblings essentially at random -- catastrophic for a
    table that IS page content (research log 0051). We detect that signature and promote the
    whole table:

    * the table has >= ``min_rows`` rows that aren't link-heavy (real data, not a nav table),
    * the classifier already kept >= ``min_kept`` of them (the table holds real content),
    * the rows are *uniform*: low length coefficient-of-variation (``max_cv``) and a small
      median length (``max_median_len``) -- i.e. data cells, NOT the long, high-variance rows
      of a forum/layout table (which must be left to per-row classification).

    Net-positive on its own merits: general/dev +0.0002 (touched docs net-positive), table
    +0.32. Operates on ``class_type`` so it runs after classification (model or heuristic).
    """
    groups = {}
    for p in paragraphs:
        if "tr" not in p.dom_path.lower().split("."):
            continue
        if not p.text.strip():
            continue
        key = _table_xpath_key(p.xpath)
        if key is None:
            continue
        groups.setdefault(key, []).append(p)

    for rows in groups.values():
        data = [p for p in rows if p.links_density() < max_link_density]
        if len(data) < min_rows:
            continue
        if sum(1 for p in data if p.class_type == "good") < min_kept:
            continue
        lengths = [len(p.text) for p in data]
        mean_len = sum(lengths) / len(lengths)
        if not mean_len:
            continue
        median_len = sorted(lengths)[len(lengths) // 2]
        if median_len > max_median_len:
            continue  # prose rows (forum posts), not data cells
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        if (variance ** 0.5) / mean_len > max_cv:
            continue  # non-uniform rows -- not a data table
        for p in data:
            p.class_type = "good"


# LaTeX math images (research log 0065). Math forums/blogs render equations as an <img>
# served by a LaTeX renderer (codecogs/mimetex/mathtex/...), with the formula in the ``alt``
# (and the ``src`` query). jusText drops <img>, so the formula vanished; the gold transcribes
# it to plaintext (``\frac 1{4-y}`` -> ``1/(4 - y)``). We do the same: detect a LaTeX-renderer
# img and replace it with a text span carrying a light LaTeX->text conversion. Scoped tightly
# to known renderer hosts so ordinary images (avatars, photos) are never touched.
_LATEX_SRC = re.compile(
    r"(codecogs|mimetex|mathtex|/latex|cgi-bin/mat|imgtex|forkosh|/cgi-bin/mimetex)", re.I)


def _latex_to_text(s):
    """Best-effort LaTeX -> readable plaintext (matches the gold's transcription style)."""
    if not s:
        return ""
    s = re.sub(r"^\$+|\$+$", "", s.strip()).strip()           # strip $...$ delimiters
    for _ in range(4):                                         # \frac variants -> a/(b)
        s = re.sub(r"\\d?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"(\1)/(\2)", s)
        s = re.sub(r"\\d?frac\s*([0-9A-Za-z])\s*\{([^{}]*)\}", r"\1/(\2)", s)
        s = re.sub(r"\\d?frac\s*\{([^{}]*)\}\s*([0-9A-Za-z])", r"(\1)/\2", s)
        s = re.sub(r"\\d?frac\s*([0-9A-Za-z])\s*([0-9A-Za-z])", r"\1/\2", s)
    s = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)", s)
    s = re.sub(r"\\left\s*([([{|])", r"\1", s)
    s = re.sub(r"\\right\s*([)\]}|])", r"\1", s)
    s = s.replace("\\cdot", "*").replace("\\times", "*").replace("\\pi", "pi")
    s = re.sub(r"\\[a-zA-Z]+", " ", s)                         # drop remaining \commands
    s = re.sub(r"[{}]", " ", s)                                # drop braces
    return re.sub(r"\s+", " ", s).strip()


# Truncated autolink URLs (research log 0069). phpBB/vBulletin shorten a long URL in the
# *displayed* anchor text -- "http://site/long-pa ... ?x=1" -- while the full URL stays in
# `href`. jusText emitted the truncated text; the gold keeps the full URL. We restore the
# href as the link text when it matches the visible prefix+suffix (so a tracking/redirect
# href that doesn't correspond to the shown URL is left alone).
_TRUNCATED_URL = re.compile(r"^(https?://\S+?)\s*\.\.\.\s*(\S+)$")


def expand_truncated_urls(dom):
    """Replace a truncated-URL anchor's text with its full href, in place."""
    for a in dom.xpath("//a[@href]"):
        if len(a):                       # has element children -> not a plain autolink
            continue
        match = _TRUNCATED_URL.match((a.text or "").strip())
        if not match:
            continue
        href = a.get("href") or ""
        if href.startswith(match.group(1)) and href.endswith(match.group(2)):
            a.text = href


def recover_latex_images(dom):
    """Replace LaTeX-renderer <img> elements with their transcribed formula text, in place."""
    import lxml.etree as etree
    try:
        from urllib.parse import unquote
    except ImportError:                                        # py2
        from urllib import unquote
    for img in dom.xpath("//img[@src]"):
        src = img.get("src") or ""
        if not _LATEX_SRC.search(src):
            continue
        alt = img.get("alt")
        if alt is None:
            match = re.search(r"[?&](?:latex|formula|chl)=?(.*)$", src)
            alt = unquote(match.group(1)) if match else ""
        text = _latex_to_text(alt)
        if not text:
            continue
        span = etree.Element("span")
        span.text = " " + text + " "
        span.tail = img.tail
        parent = img.getparent()
        if parent is not None:
            parent.replace(img, span)


# Semantic FAQ accordions (research log 0066). Some pages (off-canvas/accordion FAQs) list the
# questions TWICE -- once in a `<ul class="questions">` trigger list, once in `div.faq` blocks
# that hold the real `div.question` + `div.answer` pair. The trigger list comes first, so the
# model's dedup keeps it and DROPS the answer-block question -- orphaning every question from
# its answer. We detect the FAQ structure and (1) drop the duplicate trigger list, (2) strip
# the per-block template chrome (the "Question" label, the vote form/%). Gated on >=2 real
# question+answer blocks, so non-FAQ pages are untouched.
def restructure_faq(dom):
    """In-place: de-duplicate and de-chrome semantic FAQ blocks. No-op unless it's a FAQ."""
    faqs = dom.xpath('//div[contains(concat(" ", @class, " "), " faq ")]')
    real = [f for f in faqs
            if f.xpath('.//*[contains(concat(" ",@class," ")," question ")]//text()[normalize-space()]')
            and f.xpath('.//*[contains(concat(" ",@class," ")," answer ")]//text()[normalize-space()]')]
    if len(real) < 2:
        return
    for ul in dom.xpath('//ul[contains(concat(" ", @class, " "), " questions ")]'):
        parent = ul.getparent()
        if parent is not None:
            parent.remove(ul)
    for faq in faqs:
        for chrome in faq.xpath('.//label | .//form | .//*[contains(@class,"vote")] '
                                '| .//*[contains(@class,"helpful")]'):
            parent = chrome.getparent()
            if parent is not None:
                parent.remove(chrome)
        if not faq.xpath('.//*[contains(concat(" ",@class," ")," answer ")]//text()[normalize-space()]'):
            parent = faq.getparent()       # trigger block (no real answer) -> drop
            if parent is not None:
                parent.remove(faq)


# Blog comment authors (research log 0068). WordPress-style comments (`article/li/div`
# id="comment-N" with `.comment-content`) put the author in a `.fn`/`.comment-author-link`
# and the date in `<time>`/`.comment-meta`; jusText keeps the body but the author header is
# short/link-heavy and gets dropped, so the commenter's name never precedes the comment (the
# gold writes `*author* (date):` before each). We POST-classification prepend that marker to
# the first KEPT paragraph of each comment -- touching only already-kept comments, so we never
# resurrect a thread the model dropped. Pingbacks/trackbacks and non-name link text
# ("Permalink"/"Reply") are excluded.
_COMMENT_DATE = re.compile(
    r"[A-Z][a-z]+ \d{1,2}, \d{4}(?: at \d{1,2}:\d{2} ?[ap]m)?", re.I)
_NON_AUTHOR = re.compile(r"^(?:permalink|reply|link|quote|edit|share|report|says|\d+)$", re.I)


def _comment_author_meta(dom):
    """[(body_text, author, date)] for real WordPress comments (skips pingbacks). [] if <2."""
    comments = dom.xpath(
        '//*[self::li or self::article or self::div][starts-with(@id, "comment-")]'
        '[.//*[contains(@class,"comment-content") or contains(@class,"comment-body")]]')
    if len(comments) < 2:
        return []
    out = []
    for c in comments:
        cls = (c.get("class") or "").lower()
        if "pingback" in cls or "trackback" in cls:
            continue
        author = ""
        for t in (c.xpath('.//*[contains(@class,"fn") or contains(@class,"comment-author-link")]//text()')
                  + c.xpath('.//cite//text()')):
            t = re.sub(r"\s+", " ", t).strip()
            if t and not _NON_AUTHOR.match(t):
                author = t
                break
        date = ""
        for cand in c.xpath('.//time/@datetime | .//time//text() '
                            '| .//*[contains(@class,"comment-date") or contains(@class,"comment-meta")]//text()'):
            match = _COMMENT_DATE.search(cand)
            if match:
                date = match.group(0)
                break
        body = c.xpath('.//*[contains(@class,"comment-content") or contains(@class,"comment-body")]')
        if author and body:
            out.append((re.sub(r"\s+", " ", body[0].text_content()).strip(), author, date))
    return out


def prepend_comment_authors(paragraphs, meta):
    """In-place: insert a `*author* (date):` marker line before each comment's first KEPT line.

    The marker is its OWN paragraph (the gold puts the author on a separate line above the
    comment), matched to the FIRST kept paragraph that begins -- or, if the greeting line was
    dropped, falls within -- the comment body. Only kept comments get a marker, so a thread the
    model dropped is never resurfaced (research log 0070, fixing the 0068 mis-placement where a
    short greeting like "Hi Krishna," was skipped and the marker landed on the second line)."""
    if not meta:
        return
    used = set()
    inserts = []
    for idx, p in enumerate(paragraphs):
        if p.is_boilerplate:
            continue
        text = re.sub(r"\s+", " ", p.text).strip()
        if len(text) < 4:
            continue
        for i, (body, author, date) in enumerate(meta):
            if i in used:
                continue
            if body.startswith(text[:50]) or (len(text) >= 15 and text in body):
                marker = "*%s* (%s):" % (author, date) if date else "*%s*:" % author
                inserts.append((idx, _marker_paragraph(marker)))
                used.add(i)
                break
    if inserts:
        # The gold opens the kept comment section with a "**Comments**" heading (100% of
        # comment-keep docs) -- emit it before the first comment marker.
        inserts.insert(0, (inserts[0][0], _marker_paragraph("**Comments**")))
    for offset, (idx, marker_paragraph) in enumerate(inserts):
        paragraphs.insert(idx + offset, marker_paragraph)


def justext(html_text, stoplist, length_low=LENGTH_LOW_DEFAULT,
        length_high=LENGTH_HIGH_DEFAULT, stopwords_low=STOPWORDS_LOW_DEFAULT,
        stopwords_high=STOPWORDS_HIGH_DEFAULT, max_link_density=MAX_LINK_DENSITY_DEFAULT,
        max_heading_distance=MAX_HEADING_DISTANCE_DEFAULT, no_headings=NO_HEADINGS_DEFAULT,
        encoding=None, default_encoding=DEFAULT_ENCODING,
        enc_errors=DEFAULT_ENC_ERRORS, preprocessor=preprocessor, model=AUTO_MODEL,
        fix_encoding=True, forum_qa=True, include_comments=True, remerge=True):
    """
    Converts an HTML page into a list of classified paragraphs. Each paragraph
    is represented as instance of class ˙˙justext.paragraph.Paragraph˙˙.

    If ``model`` (a ``justext.classifier.ParagraphClassifier``) is given, the learned
    classifier re-decides each paragraph's class after the heuristic pass, using the
    heuristic output as features (see research log 0003).

    If ``fix_encoding`` is true (default) it repairs two source-text defects: mojibake in
    the input (via ftfy, only when a mojibake signature is present -- research log 0022;
    requires the optional ``ftfy`` dependency, no-op without it) and double-encoded HTML
    entities surviving into the output (research log 0023). Both are gated, so clean input
    is unaffected.

    If ``forum_qa`` is true (default) and the page is a StackExchange-engine Q&A page, it is
    rewritten so each post's role + author precede its body (research log 0031). The full
    comment thread is kept per post by default (``include_comments``, research log 0034);
    set it false for strict gold-matching benchmarking.
    """
    if model is AUTO_MODEL:
        from ._models import get_model
        model = get_model()
    if fix_encoding:
        html_text = repair_mojibake(html_text)
        html_text = escape_angle_emails(html_text)
    dom = html_to_dom(html_text, default_encoding, encoding, enc_errors)

    # Restore full URLs that phpBB/vBulletin truncated in the visible anchor text.
    expand_truncated_urls(dom)
    # Transcribe LaTeX math images to text before any path reads the DOM (forum or not).
    recover_latex_images(dom)
    # De-duplicate / de-chrome semantic FAQ accordions (no-op unless it's a FAQ page).
    restructure_faq(dom)
    # Read blog-comment authors from the raw DOM now (the header is dropped during
    # classification); applied post-classification to comments the model keeps. [] otherwise.
    comment_meta = _comment_author_meta(dom)
    # DSpace metadata table, read before preprocessing (the author links must survive); only
    # applied below if the base extraction shows the split-cell failure (research log 0082).
    dspace_lines = _dspace_metadata(dom)

    # Q&A forums (StackExchange): rewrite role+author before each post body (0031).
    if forum_qa:
        qa_paragraphs = stackexchange_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is None:
            qa_paragraphs = vbulletin_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is None:
            qa_paragraphs = phpbb_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is None:
            qa_paragraphs = smf_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is None:
            qa_paragraphs = bbpress_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is None:
            qa_paragraphs = xenforo_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is None:
            qa_paragraphs = workitmom_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is None:
            qa_paragraphs = jforum_paragraphs(dom, include_comments=include_comments)
        if qa_paragraphs is not None:
            if fix_encoding:
                decode_double_entities(qa_paragraphs)
                repair_replacement_chars(qa_paragraphs)
            return qa_paragraphs

    dom = preprocessor(dom)
    rewrite_code_tables(dom)
    rewrite_code_blocks(dom)

    paragraphs = ParagraphMaker.make_paragraphs(dom)

    classify_paragraphs(paragraphs, stoplist, length_low, length_high,
        stopwords_low, stopwords_high, max_link_density, no_headings)
    revise_paragraph_classification(paragraphs, max_heading_distance)

    if model is not None:
        model.apply(paragraphs, stoplist)

    merge_uniform_table_rows(paragraphs)
    fix_orphaned_list_markers(paragraphs)
    fix_doubled_list_numbers(paragraphs)
    prepend_comment_authors(paragraphs, comment_meta)

    if fix_encoding:
        decode_double_entities(paragraphs)
        repair_replacement_chars(paragraphs)
        clean_wiki_markup(paragraphs)

    # DSpace split-cell skins (research log 0082): the metadata table left a bare "Authors"
    # label (its link-dense value dropped). Rebuild the labeled block from the raw table.
    if dspace_lines is not None and _has_bare_dspace_label(paragraphs):
        dspace = [_marker_paragraph(line) for line in dspace_lines]
        if fix_encoding:
            decode_double_entities(dspace)
            repair_replacement_chars(dspace)
        return dspace

    # Concatenated documents (research log 0076): some WARC captures glue a redirect stub plus
    # the real page (or several pages) into one html with multiple <html>...</html>. lxml stops
    # at the first </html> and can drop the real content. Re-extract from the merged bodies and
    # keep whichever yields more content -- self-correcting, so it never regresses the cases
    # lxml already handled. Only runs on the few multi-document pages.
    if remerge:
        merged = _merge_html_documents(html_text)
        if merged is not None:
            alt = justext(merged, stoplist, length_low, length_high, stopwords_low,
                stopwords_high, max_link_density, max_heading_distance, no_headings,
                encoding, default_encoding, enc_errors, preprocessor, model, fix_encoding,
                forum_qa, include_comments, remerge=False)
            kept = sum(len(p.text) for p in paragraphs if not p.is_boilerplate)
            kept_alt = sum(len(p.text) for p in alt if not p.is_boilerplate)
            if kept_alt > kept:
                return alt

    return paragraphs


_BODY_RE = re.compile(r"<body\b[^>]*>(.*?)</body\s*>", re.S | re.I)
_HTML_END_RE = re.compile(r"</html\s*>", re.I)


def _merge_html_documents(html_text):
    """Glue the <body> contents of a multi-`<html>` page into one document, or None.

    WARC captures sometimes concatenate several documents (a redirect stub + the real page);
    this returns ``<html><body>...all bodies...</body></html>`` so a single parse sees every
    body. Returns None unless the input is text with >= 2 ``</html>`` and >= 1 ``<body>``.

    The >= 1 body case matters when a stub document has a malformed/unclosed ``<body>`` (so only
    the *real* document's body matches the pair regex) but its content sits after the first
    ``</html>``, where lxml stops -- e.g. cams.com. Merging the matched body recovers it; the
    self-correcting caller keeps the larger extraction, so a body lxml already parsed is a no-op.
    """
    if not isinstance(html_text, unicode):
        return None
    if len(_HTML_END_RE.findall(html_text)) < 2:
        return None
    bodies = _BODY_RE.findall(html_text)
    if len(bodies) < 1:
        return None
    return "<html><body>" + "".join(bodies) + "</body></html>"


_SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)


def needs_javascript_render(html, paragraphs, min_content=300,
        min_script_fraction=0.30, min_html=20000):
    """Heuristic: does this page look client-side-rendered (content only reachable via JS)?

    True only when a *large*, *script-heavy* page yields *almost no* extracted content -- the
    signature of a data-driven SPA whose body sits in a JS state blob (research log 0075). The
    caller can route those few pages to a headless browser that executes JS, then re-run
    jusText on the rendered HTML. (A non-JS text browser like lynx won't recover it -- the
    content is never in the served markup.) Pass the ``paragraphs`` from ``justext()``.

    Defaults flag ~0.3% of general/dev at 100% precision (iheart, countryliving, webdeveloper).
    Cheap: the script scan only runs once the content is already known to be tiny.
    """
    try:
        html_len = len(html)
    except TypeError:
        return False
    if html_len < min_html:
        return False
    content_chars = sum(len(p.text) for p in paragraphs if not p.is_boilerplate)
    if content_chars >= min_content:
        return False
    text = html if isinstance(html, unicode) else html.decode("latin-1", "ignore")
    script_chars = sum(len(m) for m in _SCRIPT_RE.findall(text))
    return script_chars / max(html_len, 1) > min_script_fraction
