"""切割投影片：分頁、標題與程式碼區塊"""

from briefgen.parsing.slides import parse_markdown_slides


def parse(*lines):
    return parse_markdown_slides('\n'.join(lines))


def test_split_titles_and_content():
    slides = parse('# A', '## a', '', '內容', '---', '# B', '內容 B')
    assert [(s.title, s.subtitle, s.content) for s in slides] == [
        ('A', 'a', '內容'), ('B', '', '內容 B')]


def test_heading_inside_code_block_is_code():
    [slide] = parse('# 標題', '```py', '# 註解', '## 另一行', 'x = 1', '```')
    assert slide.title == '標題'
    assert slide.content == '```py\n# 註解\n## 另一行\nx = 1\n```'


def test_separator_inside_code_block_does_not_split():
    [slide] = parse('# A', '```text', '上半', '---', '下半', '```')
    assert slide.content == '```text\n上半\n---\n下半\n```'


def test_unclosed_fence_does_not_protect_separator_or_heading():
    slides = parse('# A', '```py', '# B', '---', '# C')
    assert [(s.title, s.content) for s in slides] == [('B', '```py'), ('C', '')]


def test_separator_must_be_exactly_three_dashes():
    [slide] = parse('a', ' ---', '---- ', 'b')
    assert slide.content == 'a\n ---\n---- \nb'


def test_first_and_last_line_are_not_separators():
    [slide] = parse('---', 'a', '---')
    assert slide.content == '---\na\n---'


def test_consecutive_separators_skip_empty_slide():
    assert [s.content for s in parse('a', '---', '---', 'b')] == ['a', 'b']


def test_source_lines_around_code_block():
    slides = parse('', '# A', '', '```py', '# 註解', '```', '<b>x', '---', '', 'y')
    assert slides[0].source_lines == [4, 5, 6, 7]
    assert slides[1].source_lines == [10]
