"""樹狀圖：比卡片寬時縮小放進去，不超出、不出現水平捲軸"""

import pytest

from .helpers import ROOT, open_slides, show_slide_titled

MEASURE = """() => {
    const tree = document.querySelector('.slide.active .tree');
    const body = tree.firstElementChild;
    const t = tree.getBoundingClientRect(), b = body.getBoundingClientRect();
    return {zoom: parseFloat(body.style.zoom || '1'), treeLeft: t.left, treeRight: t.right,
            bodyLeft: b.left, bodyRight: b.right,
            hscroll: document.documentElement.scrollWidth > document.documentElement.clientWidth};
}"""


@pytest.fixture
def reference(page, build):
    open_slides(page, build(ROOT / 'docs' / '格式參考.md'))
    return page


@pytest.mark.parametrize('width', [1280, 700, 420])
def test_wide_tree_fits_inside_card(reference, width):
    reference.set_viewport_size({'width': width, 'height': 900})
    show_slide_titled(reference, '樹狀圖進階')
    m = reference.evaluate(MEASURE)
    assert m['zoom'] < 1
    assert m['bodyLeft'] >= m['treeLeft'] - 0.5
    assert m['bodyRight'] <= m['treeRight'] + 0.5
    assert not m['hscroll']


def test_narrow_tree_is_not_scaled(reference):
    show_slide_titled(reference, '樹狀圖')
    assert reference.evaluate(MEASURE)['zoom'] == 1


def test_resize_refits_current_slide(reference):
    show_slide_titled(reference, '樹狀圖')
    reference.set_viewport_size({'width': 420, 'height': 900})
    reference.wait_for_timeout(100)
    m = reference.evaluate(MEASURE)
    assert m['zoom'] < 1 and m['bodyRight'] <= m['treeRight'] + 0.5
