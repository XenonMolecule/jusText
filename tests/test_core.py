import justext


def test_form_nested_in_button_should_not_crash():
    # lxml parses the bare fragment with <button> as the document root; the Cleaner
    # (forms=True) rewrites a kill-listed root to <div> and clear()s it, then drop_tag()s
    # the now-parentless <form> -> AssertionError. The preprocessor detaches the nested
    # <form> first (the Cleaner deletes the whole <button> subtree anyway).
    paragraphs = justext.justext(
        "<button><form><p>x</p></form></button>", justext.get_stoplist("English"))

    assert paragraphs == []


def test_form_nested_in_button_inside_document_should_not_crash():
    paragraphs = justext.justext(
        "<html><body><p>hello world text</p><button><form><p>x</p></form></button>"
        "</body></html>",
        justext.get_stoplist("English"))

    assert [p.text for p in paragraphs] == ["hello world text"]


def test_words_should_be_split_by_br_tag():
    # A single <br> is a line break -> newline (research log 0025), not a space.
    paragraphs = justext.justext('abc<br/>def becoming abcdef', justext.get_stoplist("English"))

    assert [p.text for p in paragraphs] == ["abc\ndef becoming abcdef"]
