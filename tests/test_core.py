import justext
from justext.core import _is_calendar


def test_calendar_with_compatibility_digit_does_not_crash():
    # "¹".isdigit() is True but int("¹") raises ValueError; _is_calendar must not
    # crash the whole document on such cells (it uses isdecimal() instead).
    assert _is_calendar([["1", "2", "3", "4", "5", "6", "¹"]])


def test_words_should_be_split_by_br_tag():
    # A single <br> is a line break -> newline (research log 0025), not a space.
    paragraphs = justext.justext('abc<br/>def becoming abcdef', justext.get_stoplist("English"))

    assert [p.text for p in paragraphs] == ["abc\ndef becoming abcdef"]
