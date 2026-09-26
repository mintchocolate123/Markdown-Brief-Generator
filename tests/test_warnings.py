"""格式警告的輸出位置（stderr、檔名:行號）"""

import json

from briefgen.generator import PresentationGenerator

SOURCE = '\n'.join([
    '',
    '',
    '# 標題',
    '## 副標題',
    '',
    '<foo>第 6 行',
    '---',
    '',
    '```py',
    'x',
    '```',
    '<size=9>第 12 行',
    '[table]',
    '[width=full]',
    'a',
    '[c]<bad>第 16 行',
    '[/table]',
    '[tree]',
    '[id=1 o=1/2] <b 第 19 行',
    '[/tree]',
    '',
])


def build(gen, tmp_path, capsys):
    gen.generate_html(str(tmp_path / 'out.html'))
    return capsys.readouterr().err.splitlines()


def test_markdown_warnings_use_file_line_numbers(tmp_path, capsys):
    source = tmp_path / 'w.md'
    source.write_text(SOURCE, encoding='utf-8')
    gen = PresentationGenerator()
    gen.load_from_markdown(str(source))

    assert build(gen, tmp_path, capsys) == [
        f'{source}:6: 未知的格式名稱：foo，整行視為文字',
        f'{source}:12: 格式 size 的值不合法：9，整行視為文字',
        f'{source}:16: 未知的格式名稱：bad，整行視為文字',
        f'{source}:19: 樹節點不認識的設定：o=1/2',
        f'{source}:19: 行首格式缺少結尾的 >，整行視為文字',
    ]


def test_json_warnings_use_slide_and_content_line(tmp_path, capsys):
    project = tmp_path / 'p.json'
    project.write_text(json.dumps({
        'title': 'p',
        'slides': [{'title': 'a', 'content': 'ok'},
                   {'title': 'b', 'content': '第一行\n<foo>第二行'}],
    }), encoding='utf-8')
    gen = PresentationGenerator()
    gen.load_from_json(str(project))

    assert build(gen, tmp_path, capsys) == ['投影片 2 第 2 行: 未知的格式名稱：foo，整行視為文字']


def test_source_lines_are_not_saved_to_json(tmp_path):
    source = tmp_path / 'w.md'
    source.write_text(SOURCE, encoding='utf-8')
    gen = PresentationGenerator()
    gen.load_from_markdown(str(source))
    gen.save_to_json(str(tmp_path / 'p.json'))

    assert 'source_lines' not in (tmp_path / 'p.json').read_text(encoding='utf-8')
