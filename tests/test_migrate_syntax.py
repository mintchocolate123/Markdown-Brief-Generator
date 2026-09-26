"""tools/migrate_syntax.py 的單元測試"""

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
    '\\<b> 跳脫',
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
                      '[tree]', '[id=1] <imp>根', '[id=2 p=1] 子', '[/tree]',
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


def test_blocks_do_not_span_slides():
    text, _ = migrate('```\n---\n<b><i>x\n```')
    assert text == '```\n---\n<b i>x\n```'


def test_line_numbers_in_report():
    _, report = migrate('第一行\n\n<foo>x')
    assert report == ['第 3 行: 移除舊版沒有作用的格式 foo']


def test_trailing_newline_is_kept():
    assert migrate('<b><i>x\n')[0] == '<b i>x\n'
