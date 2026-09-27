"""清單語法的渲染與警告"""

import pytest

from briefgen.model import Slide
from briefgen.render.html import HTMLRenderer


def render(content):
    warnings = []
    renderer = HTMLRenderer(warn=lambda s, line, msg: warnings.append((line + 1, msg)))
    html = renderer.render_slide(Slide(content=content), 0)
    body = html[len('<div class="slide" id="slide1"><div class="slide-content">'):-len('</div></div>')]
    return body, warnings


def item(level, bullet, content):
    return (f'<div style="display:flex;align-items:baseline;margin-left:{(level + 1) * 2}em">'
            f'<span style="flex:none;width:1.2em">{bullet}</span><div>{content}</div></div>')


def test_levels_and_bullets():
    assert render('- 一\n  - 二\n    - 三\n      - 四') == (
        item(0, '•', '一') + item(1, '◦', '二') + item(2, '▪', '三') + item(3, '•', '四'), [])


def test_tab_counts_as_one_level():
    assert render('\t- 二')[0] == item(1, '◦', '二')


def test_text_level_formats_apply_to_item_text():
    assert render('- <b color=red>重點')[0] == item(0, '•', '<span style="font-weight:bold;color:#f00">重點</span>')


def test_link_in_item():
    assert render('- <link=https://a.com>網站')[0] == item(
        0, '•', '<a href="https://a.com" target="_blank" style="color:#feca57;text-decoration:underline;">網站</a>')


@pytest.mark.parametrize('line, names', [
    ('- <pivot=c>x', 'pivot'),
    ('- <imp tab=2 b>x', 'imp、tab'),
    ('- <ct>x', 'ct'),
    ('- <cont>x', 'cont'),
])
def test_block_formats_and_cont_are_ignored_with_warning(line, names):
    body, warnings = render(line)
    assert body.startswith('<div style="display:flex;align-items:baseline;margin-left:2em">')
    assert 'text-align' not in body and 'border' not in body
    assert warnings == [(1, f'清單項目不支援 {names}，已忽略')]


def test_cont_continues_list_item():
    assert render('- 前半\n<cont color=red>後半') == (
        item(0, '•', '前半<span style="color:#f00">後半</span>'), [])


def test_escaped_dash_is_literal():
    assert render('\\- 不是清單') == ('<div>- 不是清單</div>', [])


def test_dash_without_space_is_text():
    assert render('-不是清單') == ('<div>-不是清單</div>', [])


def test_escape_html_in_item():
    assert render('- a < b')[0] == item(0, '•', 'a &lt; b')


def test_items_between_normal_lines():
    assert render('前言\n- 項目\n結語') == ('<div>前言</div>' + item(0, '•', '項目') + '<div>結語</div>', [])


def test_table_cell_and_tree_node_are_not_lists():
    body, warnings = render('[table]\n- 儲存格\n[/table]\n[tree]\n[id=1] - 節點\n[/tree]')
    assert '>- 儲存格</td>' in body and '>- 節點</div>' in body
    assert 'align-items:baseline' not in body
    assert warnings == []


def test_bullet_follows_item_size_but_not_color():
    assert render('- <size=6 color=red>大字')[0] == (
        '<div style="display:flex;align-items:baseline;margin-left:2em">'
        '<span style="flex:none;width:1.2em;font-size:2em">\u2022</span>'
        '<div><span style="font-size:2em;color:#f00">大字</span></div></div>')
