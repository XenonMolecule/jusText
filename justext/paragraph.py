# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import re

from .utils import normalize_whitespace


HEADINGS_PATTERN = re.compile(r"\bh\d\b")


class Paragraph(object):
    """Object representing one block of text in HTML."""
    def __init__(self, path):
        self.dom_path = path.dom
        self.xpath = path.xpath
        self.text_nodes = []
        self.chars_count_in_links = 0
        self.tags_count = 0
        self.class_type = ""  # short | neargood | good | bad
        # Verbatim paragraphs (inside <pre>/<code>) keep their whitespace -- indentation
        # and line breaks are significant for code/ASCII content (research log 0021).
        self.verbatim = False

    @property
    def is_heading(self):
        return bool(HEADINGS_PATTERN.search(self.dom_path))

    @property
    def is_boilerplate(self):
        return self.class_type != "good"

    @property
    def text(self):
        text = "".join(self.text_nodes)
        if self.verbatim:
            # preserve indentation/newlines; only trim leading/trailing blank lines
            return text.strip("\n").rstrip()
        return normalize_whitespace(text.strip())

    def __len__(self):
        return len(self.text)

    @property
    def words_count(self):
        return len(self.text.split())

    def contains_text(self):
        return bool(self.text_nodes)

    def append_text(self, text, normalize=True):
        if normalize:
            text = normalize_whitespace(text)
        self.text_nodes.append(text)
        return text

    def stopwords_count(self, stopwords):
        return sum(word.lower() in stopwords for word in self.text.split())

    def stopwords_density(self, stopwords):
        if self.words_count == 0:
            return 0

        return self.stopwords_count(stopwords) / self.words_count

    def links_density(self):
        text_length = len(self.text)
        if text_length == 0:
            return 0

        return self.chars_count_in_links / text_length
