.. :changelog:

Changelog for jusText
=====================

4.2.0 (2026-06-25)
------------------
Validated on a fresh held-out **test** set across all five domains — no regressions vs 4.1.0;
general/test **0.8885 → 0.8927** (vs upstream jusText v3.0.2's 0.7729). New recognizable-platform
and JS-blob handlers, plus comment-attribution and malformed-HTML recovery, all gated and
self-correcting so well-formed pages are untouched.

- *FEATURE:* JS-rendered content recovered from page data, not the DOM — **CONTENTdm** digital
  libraries (``__INITIAL_STATE__``), **Ultimate Guitar** reviews (``UGAPP.store``), **Hearst
  flipbook** slideshows (``FBModel.slides``), and a research/medical **JSON-LD abstract** rescue
  (appended only when a page under-extracts).
- *FEATURE:* **vBulletin threaded mode** (posts hidden in the ``pd[]`` preview array) and
  no-``.postbit`` skins; **Ask MetaFilter**; **AnsPress** no longer misfires the StackExchange path.
- *FEATURE:* Comment attribution for more WordPress/Blogger themes (``.comment-author``) and
  Movable Type; duplicate-byline cleanup.
- *BUG FIX:* Recover content after a **premature** ``</html>`` close (self-correcting re-merge);
  fix words glued at inline ``<img>`` / block ``<address>`` boundaries; drop dangling UI-label
  paragraphs.

4.1.0 (2026-06-25)
------------------
LLM-distilled main-content extraction fork (``XenonMolecule/jusText``). Tuned against an
LLM-distilled gold benchmark; validated on held-out dev/dev2/dev3 with a strict no-regression bar.

- *FEATURE:* Recognizable-platform handlers that move the author/role to the front and strip
  chrome: StackExchange, vBulletin, phpBB, SMF, bbPress, XenForo, JForum, Drupal forums, **Ask
  MetaFilter**, **DSpace** repositories, and **CONTENTdm** digital libraries (OCR/metadata pulled
  from the client-side ``__INITIAL_STATE__`` JSON).
- *FEATURE:* Comment attribution for WordPress and **Movable Type** blog threads.
- *BUG FIX:* Recover content lost to malformed HTML — concatenated documents and a **premature**
  ``</html>`` **close** — via a self-correcting re-merge that never regresses well-formed pages.
- *BUG FIX:* Words glued at inline ``<img>`` / block ``<address>`` boundaries; dangling UI-label
  paragraphs ("By"/"Share"/"Read More"); CONTENTdm Private-Use-Area paragraph markers.
- *PACKAGING:* Bundled classifier with fastText auto-download; pip-installable fork.

3.0.2 (2025-02-25)
------------------
- *BUG FIX:* Handle urllib imports in Python 2 and 3 correctly `#51 <https://github.com/miso-belica/jusText/pull/51>`_.

3.0.1 (2024-05-09)
------------------
- *BUG FIX:* Fix issue with new version of lxml `#48 <https://github.com/miso-belica/jusText/pull/48>`_.

3.0.0 (2021-10-21)
------------------
- *INCOMPATIBLE CHANGE:* Dropped support for Python 3.4 and below.
- *BUG FIX:* Don't join words separated only by ``<br>`` tag.
- *BUG FIX:* List available stop-lists alphabetically.

2.2.0 (2016-03-06)
------------------
- *INCOMPATIBLE CHANGE:* Stop words are case insensitive.
- *INCOMPATIBLE CHANGE:* Dropped support for Python 3.2
- *BUG FIX:* Preserve new lines from original text in paragraphs.

2.1.1 (2014-05-27)
------------------
- *BUG FIX:* Function ``decode_html`` now respects parameter ``errors`` when falling to ``default_encoding`` `#9 <https://github.com/miso-belica/jusText/issues/9>`_.

2.1.0 (2014-01-25)
------------------
- *FEATURE:* Added XPath selector to the paragrahs. XPath selector is also available in detailed output as ``xpath`` attribute of ``<p>`` tag `#5 <https://github.com/miso-belica/jusText/pull/5>`_.

2.0.0 (2013-08-26)
------------------
- *FEATURE:* Added pluggable DOM preprocessor.
- *FEATURE:* Added support for Python 3.2+.
- *INCOMPATIBLE CHANGE:* Paragraphs are instances of
  ``justext.paragraph.Paragraph``.
- *INCOMPATIBLE CHANGE:* Script 'justext' removed in favour of
  command ``python -m justext``.
- *FEATURE:* It's possible to enter an URI as input document in CLI.
- *FEATURE:* It is possible to pass unicode string directly.

1.2.0 (2011-08-08)
------------------
- *FEATURE:* Character counts used instead of word counts where possible in
  order to make the algorithm work well in the language independent
  mode (without a stoplist) for languages where counting words is
  not easy (Japanese, Chinese, Thai, etc).
- *BUG FIX:* More robust parsing of meta tags containing the information about
  used charset.
- *BUG FIX:* Corrected decoding of HTML entities &#128; to &#159;

1.1.0 (2011-03-09)
------------------
- First public release.
