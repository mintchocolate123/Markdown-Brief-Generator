"""寫作慣例：簡報的每一頁在 1280×720（16:9 全螢幕）扣掉導覽列後不需要捲動"""

import os

import pytest

from briefgen.parsing.slides import parse_markdown_slides

from .helpers import GITHUB_NOTICES, ROOT, open_slides

VIEWPORT = {'width': 1280, 'height': 720}


def is_deck(path):
    """有 --- 分頁（切出兩張以上投影片）的是簡報；沒有分頁的是一般閱讀文件，不檢查尺寸"""
    return len(parse_markdown_slides(path.read_text(encoding='utf-8'))) > 1


DECKS = sorted(
    str(p.relative_to(ROOT)).replace('\\', '/')
    for p in [*(ROOT / 'docs').rglob('*.md'), *(ROOT / 'examples').rglob('*.md')]
    if is_deck(p)
)

# 每一頁的剩餘高度（負數為超出）
MARGINS = """() => [...document.querySelectorAll('.slide')].map((slide, i) => {
    showSlide(i);
    const limit = window.innerHeight - document.querySelector('.navigation').offsetHeight;
    return {page: i + 1, title: slide.querySelector('h1')?.textContent || '',
            margin: Math.floor(limit - slide.getBoundingClientRect().bottom)};
})"""


def _used_fonts(page):
    """內文實際使用的字型（Chromium 回報）"""
    cdp = page.context.new_cdp_session(page)
    cdp.send('DOM.enable')
    cdp.send('CSS.enable')
    root = cdp.send('DOM.getDocument')['root']['nodeId']
    node = cdp.send('DOM.querySelector', {'nodeId': root, 'selector': '.slide.active .slide-content > div'})['nodeId']
    return sorted({f['familyName'] for f in cdp.send('CSS.getPlatformFontsForNode', {'nodeId': node})['fonts']})


def _report_on_github(path, fonts, margins):
    """在 GitHub Actions 上把字型與最小餘裕記成 notice（沒有登入也能從 API 讀到）"""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return
    tight = sorted(margins, key=lambda m: m['margin'])[:5]
    detail = '、'.join(f"{m['page']}:{m['title']}={m['margin']}px" for m in tight)
    GITHUB_NOTICES.append(f'::notice title=fit {path}::字型 {"/".join(fonts)}；最小餘裕 {detail}')


def test_decks_are_detected():
    assert {'docs/格式參考.md', 'examples/example.md', 'examples/template.md'} <= set(DECKS)
    assert 'docs/使用指南.md' not in DECKS


@pytest.mark.parametrize('path', DECKS)
def test_every_slide_fits_1280x720(page, build, path):
    page.set_viewport_size(VIEWPORT)
    open_slides(page, build(ROOT / path))
    margins = page.evaluate(MARGINS)
    _report_on_github(path, _used_fonts(page), margins)
    overflow = [f"{path} 第 {m['page']} 頁（{m['title']}）超出 {-m['margin']}px"
                for m in margins if m['margin'] < 0]
    assert overflow == []
