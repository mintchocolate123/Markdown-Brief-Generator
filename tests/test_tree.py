"""樹狀圖渲染：任意深度、子節點格式、成環"""

from briefgen.model import Slide, SlideTheme
from briefgen.render.html import HTMLRenderer

NODE = ('background:rgba(255,255,255,.15);padding:8px 16px;border-radius:20px;'
        'display:inline-block;margin:5px;border:2px solid rgba(255,255,255,.3);')


def render(*lines):
    return HTMLRenderer(SlideTheme()).render_slide(Slide(content='\n'.join(['[tree]', *lines, '[/tree]'])), 0)


def test_every_level_is_rendered():
    html = render('[id=1] 一', '[id=2 p=1] 二', '[id=3 p=2] 三', '[id=4 p=3] 四', '[id=5 p=4] 五')
    for text in '一二三四五':
        assert f'>{text}</div>' in html


def test_deeper_nodes_are_nested_under_their_parent():
    html = render('[id=1] 一', '[id=2 p=1] 二', '[id=3 p=2] 三')
    assert html.index('>二</div>') < html.index('>三</div>')
    # 第三層放在第二層節點之後的子節點列裡
    after_two = html[html.index('>二</div>'):]
    assert after_two.index('display:flex;gap:20px') < after_two.index('>三</div>')


def test_child_node_keeps_its_own_formats():
    html = render('[id=1] 根', '[id=2 p=1] <color=red b>子')
    assert f'<div style="{NODE}color:#f00;font-weight:bold;">子</div>' in html


def test_parent_cycle_does_not_recurse_forever():
    # 重複的 id=1 讓「甲」的子節點指回祖先：根(1) -> 甲(2) -> 環(1) -> 甲 ...
    html = render('[id=1] 根', '[id=2 p=1] 甲', '[id=1 p=2] 環')
    assert html.count('>甲</div>') == 1
    assert '>環</div>' not in html
