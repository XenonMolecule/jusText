# -*- coding: utf-8 -*-

"""
Copyright (c) 2011 Jan Pomikalek

This software is licensed as described in the file LICENSE.rst.
"""

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import re
import lxml.html
import lxml.sax

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

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
    'td', 'th', 'li', 'dd', 'dt', 'option', 'caption',
})
DEFAULT_ENCODING = 'utf8'
DEFAULT_ENC_ERRORS = 'replace'
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

    try:
        dom = lxml.html.fromstring(decoded_html, parser=lxml.html.HTMLParser())
    except ValueError:
        # Unicode strings with encoding declaration are not supported.
        # for XHTML files with encoding declaration, use the declared encoding
        dom = lxml.html.fromstring(html, parser=lxml.html.HTMLParser())

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
        self._start_new_pragraph()

    def _start_new_pragraph(self):
        if self.paragraph and self.paragraph.contains_text():
            self.paragraphs.append(self.paragraph)

        self.paragraph = Paragraph(self.path)

    def startElementNS(self, name, qname, attrs):
        name = name[1]
        self.path.append(name)

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
                self.paragraph.append_text(' ')
            self.br = bool(name == "br")
            if self.br:
                # A single <br> is a line break: emit a newline (the gold respects
                # <br> line structure -- addresses, contact blocks, <br>-separated
                # lists/publications). normalize_whitespace keeps the \n because the
                # run contains a newline (research log 0025). <br><br> still becomes a
                # paragraph break via the name=="br" and self.br branch above.
                self.paragraph.append_text('\n')
            elif name == 'a':
                self.link = True
            self.paragraph.tags_count += 1

    def endElementNS(self, name, qname):
        name = name[1]
        self.path.pop()

        if name in ("pre", "textarea") and self.pre > 0:
            self.pre -= 1
        if name in PARAGRAPH_TAGS:
            self._start_new_pragraph()
        elif name in SEPARATOR_TAGS:
            self.paragraph.append_text(' ')
        if name == 'a':
            self.link = False

    def endDocument(self):
        self._start_new_pragraph()

    def characters(self, content):
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
            text = self.paragraph.append_text(content)

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


def justext(html_text, stoplist, length_low=LENGTH_LOW_DEFAULT,
        length_high=LENGTH_HIGH_DEFAULT, stopwords_low=STOPWORDS_LOW_DEFAULT,
        stopwords_high=STOPWORDS_HIGH_DEFAULT, max_link_density=MAX_LINK_DENSITY_DEFAULT,
        max_heading_distance=MAX_HEADING_DISTANCE_DEFAULT, no_headings=NO_HEADINGS_DEFAULT,
        encoding=None, default_encoding=DEFAULT_ENCODING,
        enc_errors=DEFAULT_ENC_ERRORS, preprocessor=preprocessor, model=None,
        fix_encoding=True):
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
    """
    if fix_encoding:
        html_text = repair_mojibake(html_text)
        html_text = escape_angle_emails(html_text)
    dom = html_to_dom(html_text, default_encoding, encoding, enc_errors)
    dom = preprocessor(dom)

    paragraphs = ParagraphMaker.make_paragraphs(dom)

    classify_paragraphs(paragraphs, stoplist, length_low, length_high,
        stopwords_low, stopwords_high, max_link_density, no_headings)
    revise_paragraph_classification(paragraphs, max_heading_distance)

    if model is not None:
        model.apply(paragraphs, stoplist)

    if fix_encoding:
        decode_double_entities(paragraphs)

    return paragraphs
