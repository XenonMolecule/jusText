import justext
from justext.core import _is_calendar


def test_calendar_with_compatibility_digit_does_not_crash():
    # "¹".isdigit() is True but int("¹") raises ValueError; _is_calendar must not
    # crash the whole document on such cells (it uses isdecimal() instead).
    assert _is_calendar([["1", "2", "3", "4", "5", "6", "¹"]])


def test_data_table_with_xml_illegal_char_should_not_crash():
    # &#1; in a cell survives HTML parsing as U+0001, which lxml refuses in a text
    # node -- rewrite_data_tables must sanitize before assigning pre.text.
    html = (
        "<html><body>"
        "<table>"
        "<tr><th>Name</th><th>Value</th></tr>"
        "<tr><td>alpha</td><td>1</td></tr>"
        "<tr><td>beta&#1;</td><td>2</td></tr>"
        "<tr><td>gamma</td><td>3</td></tr>"
        "</table>"
        "</body></html>"
    )
    paragraphs = justext.justext(html, justext.get_stoplist("English"))

    text = "\n".join(p.text for p in paragraphs)
    assert "beta" in text
    assert "\x01" not in text


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
