import justext


def test_words_should_be_split_by_br_tag():
    # A single <br> is a line break -> newline (research log 0025), not a space.
    paragraphs = justext.justext('abc<br/>def becoming abcdef', justext.get_stoplist("English"))

    assert [p.text for p in paragraphs] == ["abc\ndef becoming abcdef"]
