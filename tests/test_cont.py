"""cont（接續上一行）的渲染與警告"""

from briefgen.model import Slide
from briefgen.render.html import HTMLRenderer


def render(content):
    warnings = []
    renderer = HTMLRenderer(warn=lambda s, line, msg: warnings.append((line + 1, msg)))
    html = renderer.render_slide(Slide(content=content), 0)
    body = html[len('<div class="slide" id="slide1"><div class="slide-content">'):-len('</div></div>')]
    return body, warnings


def test_cont_becomes_span_in_previous_div():
    assert render('第一段\n<cont color=red>紅色') == (
        '<div>第一段<span style="color:#f00">紅色</span></div>', [])


def test_cont_keeps_leading_whitespace():
    assert render('Hello\n<cont b> world')[0] == (
        '<div>Hello<span style="font-weight:bold"> world</span></div>')


def test_cont_without_formats():
    assert render('a\n<cont>b')[0] == '<div>a<span>b</span></div>'


def test_consecutive_cont_lines_share_one_div():
    assert render('a\n<cont b>b\n<cont i>c')[0] == (
        '<div>a<span style="font-weight:bold">b</span><span style="font-style:italic">c</span></div>')


def test_first_segment_text_formats_do_not_reach_cont():
    assert render('<color=red size=5 link=https://a.com>a\n<cont>b')[0] == (
        '<div><span style="color:#f00;font-size:1.5em">'
        '<a href="https://a.com" target="_blank" style="color:#feca57;text-decoration:underline;">a</a>'
        '</span><span>b</span></div>')


def test_block_formats_of_first_line_apply_to_whole_line():
    assert render('<pivot=c tab=1 color=red>a\n<cont b>b')[0] == (
        '<div style="margin-left:2em;text-align:center"><span style="color:#f00">a</span>'
        '<span style="font-weight:bold">b</span></div>')


def test_cont_inside_imp_box():
    imp = ('text-align:center;border:2px solid #feca57;border-radius:10px;padding:15px 20px;'
           'background:rgba(254,202,87,.1);margin:10px 0')
    assert render('<imp>重要\n<cont color=red>接續')[0] == (
        f'<div style="{imp}">重要<span style="color:#f00">接續</span></div>')
    assert render('<imp b>重要\n<cont>接續')[0] == (
        f'<div style="{imp}"><span style="font-weight:bold">重要</span><span>接續</span></div>')


def test_line_without_cont_is_unchanged():
    assert render('<pivot=c color=red>a')[0] == '<div style="text-align:center;color:#f00">a</div>'


def test_cont_text_level_formats():
    body, warnings = render('a\n<cont u s size=2 link=https://a.com>b')
    assert body == ('<div>a<span style="text-decoration:underline line-through;font-size:0.85em">'
                    '<a href="https://a.com" target="_blank" style="color:#feca57;text-decoration:underline;">b</a>'
                    '</span></div>')
    assert warnings == []


def test_cont_ignores_block_formats_with_warning():
    body, warnings = render('a\n<cont pivot=c tab=2 imp ct img=x.png,1,2 b>b')
    assert body == '<div>a<span style="font-weight:bold">b</span></div>'
    assert warnings == [(2, 'cont 行不支援區塊格式 pivot、tab、imp、ct、img，已忽略')]


def test_cont_after_link_and_image():
    assert render('<link=https://a.com>a\n<cont>b')[0] == (
        '<div><a href="https://a.com" target="_blank" style="color:#feca57;text-decoration:underline;">a</a>'
        '<span>b</span></div>')
    assert render('<img=x.png,1,2>\n<cont>說明')[0] == (
        '<div><img src="x.png" style="max-width:100%;border-radius:10px;"><span>說明</span></div>')


def test_cont_after_subtitle_goes_inside_subtitle_span():
    subtitle = ('font-size:1.4em;font-weight:bold;color:#feca57;border-bottom:2px solid #feca57;'
                'padding-bottom:5px;margin-bottom:10px;display:inline-block')
    assert render('<ct color=red>標題\n<cont i>補充')[0] == (
        '<div style="display:flex;align-items:flex-end;flex-wrap:wrap;gap:10px">'
        f'<span style="{subtitle}"><span style="color:#f00">標題</span>'
        '<span style="font-style:italic">補充</span></span></div>')


def test_cont_on_first_line_of_paragraph_is_normal_line():
    body, warnings = render('a\n\n<cont b>  b')
    assert body == '<div>a</div>\n<div style="font-weight:bold">b</div>'
    assert warnings == [(3, '段落第一行的 cont 沒有可接續的行，當作一般行')]


def test_cont_does_not_cross_blocks():
    body, warnings = render('a\n[table]\nx\n[/table]\n<cont>b')
    assert body.endswith('<div>b</div>')
    assert warnings == [(5, '段落第一行的 cont 沒有可接續的行，當作一般行')]


def test_cont_in_table_cell_warns():
    body, warnings = render('[table]\n標題\n[c]<cont b> 文字\n[/table]')
    assert 'font-weight:bold;">文字</td>' in body
    assert warnings == [(3, '表格儲存格不支援 cont，已忽略')]


def test_cont_in_tree_node_warns():
    body, warnings = render('[tree]\n[id=1] <cont b> 節點\n[/tree]')
    assert 'font-weight:bold;">節點</div>' in body
    assert warnings == [(2, '樹節點不支援 cont，已忽略')]
