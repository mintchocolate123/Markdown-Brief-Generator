"""tools/migrate_syntax.py 的單元測試"""

from pathlib import Path

import pytest

from migrate_syntax import migrate


def one(line):
    text, report = migrate(line)
    return text, report


@pytest.mark.parametrize('old, new', [
    ('<size<5>>大字', '<size=5>大字'),
    ('<pivot<c>><size<6>><color<orange>>標題', '<pivot=c size=6 color=orange>標題'),
    ('<b><i>粗斜體', '<b i>粗斜體'),
    ('<u><s>雙線', '<u s>雙線'),
    ('<cont color<red>>接續', '<cont color=red>接續'),
    ('<cont b> word', '<cont b> word'),
    ('<tab<2>>縮排', '<tab=2>縮排'),
    ('<link<https://a.com/?x=1>>連結', '<link=https://a.com/?x=1>連結'),
    ('<img<https://a.com/a.png,300,150>>', '<img=https://a.com/a.png,300,150>'),
    ('<color<rgb(255, 0, 0)>>紅', '<color="rgb(255, 0, 0)">紅'),
    ('<link<i>>連結', '<link=i>連結'),
    ('  <b>縮排保留', '  <b>縮排保留'),
    ('<b>   空白保留', '<b>   空白保留'),
])
def test_paragraph_tags(old, new):
    assert one(old) == (new, [])


@pytest.mark.parametrize('line', [
    '普通文字',
    '<3 沒有結尾',
    '# <b>標題不動',
    '## 副標題',
    '---',
    '',
])
def test_untouched_lines(line):
    assert one(line) == (line, [])


def test_square_brackets_with_known_formats_become_angle():
    assert one('[b]粗體') == ('<b>粗體', [])
    assert one('[b] <i>粗斜體') == ('<b i>粗斜體', [])


def test_square_brackets_with_unknown_content_stay_as_text():
    text, report = one('[注意]說明')
    assert text == '[注意]說明'
    assert report == ['第 1 行: 段落行首的 [注意] 在新語法中會顯示為文字（舊版會被隱藏）']


def test_unknown_names_are_removed_and_reported():
    text, report = one('<foo b>文字')
    assert text == '<b>文字'
    assert report == ['第 1 行: 移除舊版沒有作用的格式 foo']


def test_tag_with_only_unknown_names_is_removed():
    text, report = one('<html>文字')
    assert text == '文字'
    assert report == ['第 1 行: 移除舊版沒有作用的格式 html']


@pytest.mark.parametrize('old, removed', [
    ('<size<9>>x', 'size<9>'),
    ('<pivot<x>>x', 'pivot<x>'),
    ('<tab<abc>>x', 'tab<abc>'),
    ('<b<1>>x', 'b<1>'),
    ('<img<a.png,1>>x', 'img<a.png,1>'),
])
def test_invalid_values_are_removed_and_reported(old, removed):
    text, report = one(old)
    assert text == 'x'
    assert report == [f'第 1 行: 移除舊版沒有作用的格式 {removed}']


def test_empty_tag_is_removed():
    assert one('<>文字') == ('文字', ['第 1 行: 移除空的 <>'])


def test_new_syntax_is_idempotent():
    for line in ['<pivot=c size=6 color=orange>標題', '<color="rgb(1, 2, 3)" b>x',
                 '<link=https://a.com/?x=1>x']:
        assert one(line) == (line, [])


def test_new_syntax_blocks_are_idempotent():
    text = '\n'.join(['[table]', '[width=full]', '<b i>x', '[/table]',
                      '[tree]', '[width=full]', '[id=1] <imp>根', '[id=2 p=1] 子', '[/tree]',
                      '```py', '[width=full]', '```'])
    assert migrate(text) == (text, [])


def test_unknown_new_style_name_is_removed():
    assert one('<width=full>x') == ('x', ['第 1 行: 移除舊版沒有作用的格式 width=full'])


def test_table_block():
    old = '\n'.join([
        '[table]',
        '[width<400px>]',
        '<imp>標題',
        '[c]<b><i>多個角括號',
        '[c]<imp> 前導空白',
        '[注意]方括號開頭',
        '[c]',
        '[/table]',
    ])
    new = '\n'.join([
        '[table]',
        '[width=400px]',
        '<imp>標題',
        '[c]<b i>多個角括號',
        '[c]<imp> 前導空白',
        '[注意]方括號開頭',
        '[c]',
        '[/table]',
    ])
    assert migrate(old) == (new, [])


def test_tree_block():
    old = '\n'.join([
        '[tree]',
        '[width<full>]',
        '[id<1> imp] <b><i>根',
        '[id<2> p<1> o<1/2>] <imp> 子',
        '不是節點的行',
        '[/tree]',
    ])
    new = '\n'.join([
        '[tree]',
        '[width=full]',
        '[id=1] <b i>根',
        '[id=2 p=1] <imp> 子',
        '不是節點的行',
        '[/tree]',
    ])
    text, report = migrate(old)
    assert text == new
    assert report == [
        '第 3 行: 移除樹節點的 imp',
        '第 4 行: 移除樹節點的 o<1/2>',
    ]


def test_code_block_only_converts_width():
    old = '\n'.join(['```cpp', '[width<600px>]', '#include <vector>', '<b>', '[b]x', '```'])
    new = '\n'.join(['```cpp', '[width=600px]', '#include <vector>', '<b>', '[b]x', '```'])
    assert migrate(old) == (new, [])


def test_unclosed_block_is_treated_as_paragraph():
    text, _ = migrate('[table]\n<b><i>x')
    assert text == '[table]\n<b i>x'


def test_separator_inside_code_block_does_not_split():
    text = '```\n---\n<b><i>x\n```'
    assert migrate(text) == (text, [])


def test_blocks_do_not_span_slides():
    text, _ = migrate('[table]\n---\n<b><i>x\n[/table]')
    assert text == '[table]\n---\n<b i>x\n[/table]'


def test_line_numbers_in_report():
    _, report = migrate('第一行\n\n<foo>x')
    assert report == ['第 3 行: 移除舊版沒有作用的格式 foo']


def test_trailing_newline_is_kept():
    assert migrate('<b><i>x\n')[0] == '<b i>x\n'


FIXTURES = Path(__file__).resolve().parent / 'fixtures'


@pytest.mark.parametrize('name, expected_report', [
    ('example', []),
    ('格式參考', []),
    ('edge_cases', [
        '第 19 行: 段落行首的 [注意] 在新語法中會顯示為文字（舊版會被隱藏）',
        '第 65 行: 移除樹節點的 imp',
        '第 66 行: 移除樹節點的 o<1/2>',
        '第 67 行: 移除樹節點的 o<2/2>',
        '第 134 行: 行首的 \\- 在新語法會顯示為 -（舊版會顯示反斜線）',
    ]),
])
def test_fixtures_convert_to_new_versions(name, expected_report):
    old = (FIXTURES / 'old' / f'{name}.md').read_text(encoding='utf-8')
    new = (FIXTURES / 'new' / f'{name}.md').read_text(encoding='utf-8')
    assert migrate(old) == (new, expected_report)


@pytest.mark.parametrize('name', ['example', '格式參考', 'edge_cases'])
def test_converting_new_fixtures_again_changes_nothing(name):
    new = (FIXTURES / 'new' / f'{name}.md').read_text(encoding='utf-8')
    text, report = migrate(new)
    assert text == new
    # 只可能再次出現「[...] 會顯示為文字」的提醒，不會移除任何內容
    assert not [line for line in report if '移除' in line]


@pytest.mark.parametrize('line, char', [('\\<b>字面', '<'), ('\\- 字面', '-')])
def test_leading_backslash_escape_is_reported(line, char):
    assert one(line) == (line, [f'第 1 行: 行首的 \\{char} 在新語法會顯示為 {char}（舊版會顯示反斜線）'])


def test_backslash_dash_in_table_cell_is_not_reported():
    text = '[table]\n\\- 儲存格\n[/table]'
    assert migrate(text) == (text, [])


INLINE_HINT = '不會套用格式（只有行首的 <...> 有效），請手動拆成 cont 行'


@pytest.mark.parametrize('line, converted, tags', [
    ('<tab<1>>文字要用<color<yellow>>引號<cont>包起來', '<tab=1>文字要用<color<yellow>>引號<cont>包起來',
     '<color<yellow>>、<cont>'),
    ('<tab<1>>它的意思是：<b>把右邊的值</b>', '<tab=1>它的意思是：<b>把右邊的值</b>', '<b>、</b>'),
    ('沒有行首格式<i>斜體', '沒有行首格式<i>斜體', '<i>'),
    ('<b>新語法寫在行中<color=red>也無效', '<b>新語法寫在行中<color=red>也無效', '<color=red>'),
    ('<b i>多個<size<5> b>項目', '<b i>多個<size<5> b>項目', '<size<5> b>'),
])
def test_inline_tags_are_reported_not_converted(line, converted, tags):
    assert one(line) == (converted, [f'第 1 行: 行中間的 {tags} {INLINE_HINT}'])


@pytest.mark.parametrize('line', [
    'a < b > c',
    'std::vector<int> v',
    '<3 我愛你 <3',
    'x <未知> y',
    '# 標題 <b>不檢查',
])
def test_text_that_is_not_an_inline_tag(line):
    assert one(line) == (line, [])


def test_inline_tags_in_code_block_are_ignored():
    text = '```html\n文字<b>粗體</b>\n```'
    assert migrate(text) == (text, [])


def test_list_item_leading_tag_is_converted_not_reported():
    assert one('- <size<5>><b>大字') == ('- <size=5 b>大字', [])
    assert one('  - 項目<b>行中') == ('  - 項目<b>行中', [f'第 1 行: 行中間的 <b> {INLINE_HINT}'])


def test_inline_tags_in_cells_and_tree_nodes():
    text, report = migrate('[table]\n[c]前<b>後\n[/table]\n[tree]\n[id<1>] 根<i>x\n[/tree]')
    assert text == '[table]\n[c]前<b>後\n[/table]\n[tree]\n[id=1] 根<i>x\n[/tree]'
    assert report == [f'第 2 行: 行中間的 <b> {INLINE_HINT}', f'第 5 行: 行中間的 <i> {INLINE_HINT}']


def test_inline_tag_after_escaped_leading_bracket():
    assert one('\\<b> 與 <i>斜體')[1] == [
        '第 1 行: 行首的 \\< 在新語法會顯示為 <（舊版會顯示反斜線）',
        f'第 1 行: 行中間的 <i> {INLINE_HINT}',
    ]
