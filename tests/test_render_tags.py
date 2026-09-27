"""行首格式在段落、儲存格、樹節點中的渲染結果"""

import pytest

from briefgen.model import Slide
from briefgen.render.html import HTMLRenderer

LINK_STYLE = 'color:#feca57;text-decoration:underline;'
SUBTITLE_STYLE = ('font-size:1.4em;font-weight:bold;color:#feca57;border-bottom:2px solid #feca57;'
                  'padding-bottom:5px;margin-bottom:10px;display:inline-block')
IMP_STYLE = ('text-align:center;border:2px solid #feca57;border-radius:10px;padding:15px 20px;'
             'background:rgba(254,202,87,.1);margin:10px 0')


def render(content):
    warnings = []
    renderer = HTMLRenderer(warn=lambda s, line, msg: warnings.append((line + 1, msg)))
    html = renderer.render_slide(Slide(content=content), 0)
    body = html[len('<div class="slide" id="slide1"><div class="slide-content">'):-len('</div></div>')]
    return body, warnings


@pytest.mark.parametrize('line, html', [
    ('<b>x', '<div style="font-weight:bold">x</div>'),
    ('<bold>x', '<div style="font-weight:bold">x</div>'),
    ('<i>x', '<div style="font-style:italic">x</div>'),
    ('<italic>x', '<div style="font-style:italic">x</div>'),
    ('<u>x', '<div style="text-decoration:underline">x</div>'),
    ('<underline>x', '<div style="text-decoration:underline">x</div>'),
    ('<s>x', '<div style="text-decoration:line-through">x</div>'),
    ('<strike>x', '<div style="text-decoration:line-through">x</div>'),
    ('<size=3>x', '<div style="font-size:1em">x</div>'),
    ('<color=orange>x', '<div style="color:#ffa500">x</div>'),
    ('<tab=2>x', '<div style="margin-left:4em">x</div>'),
    ('<pivot=r>x', '<div style="text-align:right">x</div>'),
    ('<imp>x', f'<div style="{IMP_STYLE}">x</div>'),
    ('<ct>x', f'<div style="display:flex;align-items:flex-end;flex-wrap:wrap;gap:10px"><span style="{SUBTITLE_STYLE}">x</span></div>'),
    ('<link=https://a.com/?x=1>x', f'<div><a href="https://a.com/?x=1" target="_blank" style="{LINK_STYLE}">x</a></div>'),
    ('<img=https://a.com/a.png,300,150>', '<div><img src="https://a.com/a.png" style="width:300px;aspect-ratio:300/150;height:auto;object-fit:contain;max-width:100%;border-radius:10px;"></div>'),
    ('<pivot=c size=6 color=orange>大標題', '<div style="text-align:center;font-size:2em;color:#ffa500">大標題</div>'),
])
def test_each_format(line, html):
    assert render(line) == (html, [])


def test_quoted_value():
    assert render('<color="rgb(255, 0, 0)">x') == ('<div style="color:rgb(255, 0, 0)">x</div>', [])


def test_unknown_name_renders_line_as_text():
    assert render('第一行\n<b foo>x') == (
        '<div>第一行</div><div>&lt;b foo&gt;x</div>',
        [(2, '未知的格式名稱：foo，整行視為文字')])


def test_escape_renders_literal_bracket():
    assert render('\\<b>x') == ('<div>&lt;b&gt;x</div>', [])


def test_old_multi_tag_warns():
    assert render('<b><i>x') == (
        '<div style="font-weight:bold">&lt;i&gt;x</div>',
        [(1, '格式後面的 <...> 會顯示為文字，可能是舊語法（一行只能有一個 <...>）')])


def test_square_brackets_in_paragraph_are_text():
    assert render('[b]x') == ('<div>[b]x</div>', [])


def test_cell_formats_escape_and_unknown():
    body, warnings = render('[table]\n標題\n[c]<color=red b>紅\n\\<b>字面\n[c]<foo>未知\n[/table]')
    assert 'color:#ff9999;font-weight:bold;">紅</td>' in body
    assert 'text-align:center;">&lt;b&gt;字面</td>' in body
    assert 'text-align:center;">&lt;foo&gt;未知</td>' in body
    assert warnings == [(5, '未知的格式名稱：foo，整行視為文字')]


def test_tree_node_formats_escape_and_unknown():
    body, warnings = render('[tree]\n[id=1] <color=red>根\n[id=2 p=1] \\<b>字面\n[id=3 p=1] <foo>未知\n[/tree]')
    assert 'color:#ff9999;">根</div>' in body
    assert '&lt;b&gt;字面</div>' in body
    assert '&lt;foo&gt;未知</div>' in body
    assert warnings == [(4, '未知的格式名稱：foo，整行視為文字')]


def test_width_settings():
    assert 'width:100%;' in render('[table]\n[width=full]\na\n[/table]')[0]
    assert 'min-width:400px;' in render('[table]\n[width=400px]\na\n[/table]')[0]
    assert 'min-width:600px;' in render('```py\n[width=600px]\nx\n```')[0]


def test_tree_unknown_setting_is_ignored_with_warning():
    body, warnings = render('[tree]\n[id=1 o=1/2] 根\n[/tree]')
    assert '>根</div>' in body
    assert warnings == [(2, '樹節點不認識的設定：o=1/2')]


@pytest.mark.parametrize('title, subtitle, header', [
    ('主', '副', '<h1>主</h1><p class="subtitle">副</p>'),
    ('主', '', '<h1>主</h1><p class="subtitle"></p>'),
    ('', '副', '<h1>副</h1><p class="subtitle"></p>'),
])
def test_slide_header(title, subtitle, header):
    html = HTMLRenderer().render_slide(Slide(title=title, subtitle=subtitle, content='x'), 0)
    assert f'<div class="slide-header">{header}</div>' in html


def test_no_header_without_title_and_subtitle():
    html = HTMLRenderer().render_slide(Slide(content='x'), 0)
    assert 'slide-header' not in html
