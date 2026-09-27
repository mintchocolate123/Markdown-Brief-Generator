"""語法高亮：各語言的註解、字串、關鍵字，以及語言標記的解析"""

import pytest

from briefgen.highlighter import SyntaxHighlighter
from briefgen.parsing.blocks import MarkdownParser


def hl(code, lang):
    return SyntaxHighlighter().highlight(code, lang)


def span(color, text, bold=False):
    return f'<span style="color:{color}{";font-weight:bold" if bold else ""}">{text}</span>'


@pytest.mark.parametrize('fence, lang', [
    ('```c++', 'cpp'), ('```c#', 'cs'), ('```cpp', 'cpp'), ('```python', 'py'),
    ('```sh', 'bash'), ('```shell', 'bash'), ('```bash', 'bash'), ('```htm', 'html'),
    ('```css', 'css'), ('```json', 'json'), ('```', 'text'),
])
def test_fence_language(fence, lang):
    _, blocks, _ = MarkdownParser().parse(f'{fence}\nx\n```')
    assert blocks[0]['lang'] == lang


def test_unsupported_language_is_escaped_plain_text():
    assert hl('<a> "b"', 'rust') == ('&lt;a&gt; "b"', '#2d2d2d')


def test_python_floor_division_is_not_a_comment():
    code, _ = hl('x = a // 2  # 註解', 'py')
    assert code == f'x = a // {span("#bd93f9", "2")}  {span("#6272a4", "# 註解")}'


def test_bash():
    code, bg = hl('# 設定\nif [ "$NAME" ]; then echo ${HOME} https://a.com/x; fi', 'bash')
    assert bg == '#1e1e1e'
    assert code == (
        f'{span("#6a9955", "# 設定")}\n'
        f'{span("#569cd6", "if", True)} [ {span("#ce9178", chr(34) + "$NAME" + chr(34))} ]; '
        f'{span("#569cd6", "then", True)} {span("#569cd6", "echo", True)} {span("#9cdcfe", "${HOME}")} '
        f'https://a.com/x; {span("#569cd6", "fi", True)}')


def test_bash_hash_inside_word_is_not_a_comment():
    code, _ = hl('echo a#b $#', 'bash')
    assert '#b' in code and span('#9cdcfe', '$#') in code and '#6a9955' not in code


def test_html():
    code, _ = hl('<!-- 註解 -->\n<a href="x.html">連結</a>', 'html')
    assert code == (
        f'{span("#6a9955", "&lt;!-- 註解 --&gt;")}\n'
        f'&lt;{span("#569cd6", "a")} {span("#9cdcfe", "href")}={span("#ce9178", chr(34) + "x.html" + chr(34))}&gt;'
        f'連結&lt;{span("#569cd6", "/a")}&gt;')


def test_css():
    code, _ = hl('/* 註解 */\n.box, a:hover {\n  color: #fff;\n  margin: 0 10px;\n}', 'css')
    assert code == (
        f'{span("#6a9955", "/* 註解 */")}\n'
        f'{span("#d7ba7d", ".box, a:hover ")}{{\n'
        f'{span("#9cdcfe", "  color")}: {span("#b5cea8", "#fff")};\n'
        f'{span("#9cdcfe", "  margin")}: {span("#b5cea8", "0")} {span("#b5cea8", "10px")};\n}}')


def test_css_units_and_percent():
    code, _ = hl('a {\n  width: 50%;\n  font-size: 1.5em;\n}', 'css')
    assert span('#b5cea8', '50%') in code and span('#b5cea8', '1.5em') in code


def test_json():
    code, _ = hl('{"name": "值", "n": 1.5, "ok": true, "x": null}', 'json')
    assert code == (
        f'{{{span("#9cdcfe", chr(34) + "name" + chr(34))}: {span("#ce9178", chr(34) + "值" + chr(34))}, '
        f'{span("#9cdcfe", chr(34) + "n" + chr(34))}: {span("#b5cea8", "1.5")}, '
        f'{span("#9cdcfe", chr(34) + "ok" + chr(34))}: {span("#569cd6", "true", True)}, '
        f'{span("#9cdcfe", chr(34) + "x" + chr(34))}: {span("#569cd6", "null", True)}}}')
