"""寫作慣例：每一頁在 1280×720（16:9 全螢幕）扣掉導覽列後不需要捲動"""

import pytest

from .helpers import ROOT, open_slides

VIEWPORT = {'width': 1280, 'height': 720}

# 一般閱讀用的文件（沒有用 --- 分頁），不是簡報，不套用一頁放得下的標準
READING_DOCUMENTS = {'docs/使用指南.md', 'docs/語法速查.md', 'docs/開發.md'}

DECKS = sorted(
    str(p.relative_to(ROOT)).replace('\\', '/')
    for p in [*(ROOT / 'docs').rglob('*.md'), *(ROOT / 'examples').rglob('*.md')]
)

OVERFLOW = """() => [...document.querySelectorAll('.slide')].map((slide, i) => {
    showSlide(i);
    const limit = window.innerHeight - document.querySelector('.navigation').offsetHeight;
    return {page: i + 1, title: slide.querySelector('h1')?.textContent || '',
            over: Math.ceil(slide.getBoundingClientRect().bottom - limit)};
}).filter(r => r.over > 0)"""


@pytest.mark.parametrize('path', [d for d in DECKS if d not in READING_DOCUMENTS])
def test_every_slide_fits_1280x720(page, build, path):
    page.set_viewport_size(VIEWPORT)
    open_slides(page, build(ROOT / path))
    overflow = page.evaluate(OVERFLOW)
    assert [f"{path} 第 {r['page']} 頁（{r['title']}）超出 {r['over']}px" for r in overflow] == []
