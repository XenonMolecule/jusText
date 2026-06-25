# -*- coding: utf-8 -*-

"""
Copyright (c) 2011 Jan Pomikalek

This software is licensed as described in the file LICENSE.rst.
"""

from __future__ import absolute_import

from .utils import get_stoplists, get_stoplist
from .core import justext, needs_javascript_render
from .classifier import ParagraphClassifier
from ._models import get_model, download_fasttext


__version__ = "4.0.0"
