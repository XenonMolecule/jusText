import justext


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


def test_words_should_be_split_by_br_tag():
    # A single <br> is a line break -> newline (research log 0025), not a space.
    paragraphs = justext.justext('abc<br/>def becoming abcdef', justext.get_stoplist("English"))

    assert [p.text for p in paragraphs] == ["abc\ndef becoming abcdef"]
