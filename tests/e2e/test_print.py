"""列印 / PDF：每張投影片一頁 16:9、隱藏導覽、保留背景、太高或太寬的內容縮小放進一頁"""

import pytest

from .helpers import ROOT, open_slides

pdfium = pytest.importorskip('pypdfium2')

PAGE_POINTS = (960.0, 540.0)  # 13.333in x 7.5in


@pytest.fixture
def reference(page, build):
    open_slides(page, build(ROOT / 'docs' / '格式參考.md'))
    return page


def pdf_pages(page):
    document = pdfium.PdfDocument(page.pdf(prefer_css_page_size=True, print_background=True))
    return [(p.get_size(), p.get_textpage().get_text_range()) for p in document]


def test_pdf_has_one_16_9_page_per_slide(reference):
    slides = reference.evaluate("document.querySelectorAll('.slide').length")
    pages = pdf_pages(reference)
    assert len(pages) == slides == 26
    assert all(size == pytest.approx(PAGE_POINTS, abs=0.5) for size, _ in pages)
    assert '現在你知道所有格式了' in pages[-1][1]
    assert not any('下一張' in text or '複製' in text for _, text in pages)


def test_print_media_hides_controls_and_keeps_colors(reference):
    reference.emulate_media(media='print')
    display = reference.evaluate("""() => {
        const d = s => getComputedStyle(document.querySelector(s)).display;
        return {nav: d('.navigation'), progress: d('.progress-bar'), blackout: d('#blackout'),
                copy: d('.slide button'),
                slides: [...document.querySelectorAll('.slide')].every(s => getComputedStyle(s).display === 'block'),
                adjust: getComputedStyle(document.querySelector('.slide')).printColorAdjust};
    }""")
    assert display == {'nav': 'none', 'progress': 'none', 'blackout': 'none', 'copy': 'none',
                       'slides': True, 'adjust': 'exact'}


def test_tall_slide_is_scaled_to_fit_page_and_restored(page, build):
    open_slides(page, build('# 很長\n' + '\n'.join(f'第 {n} 行' for n in range(80))))
    page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    fit = page.evaluate("""() => {
        const s = document.querySelector('.slide');
        return {zoom: parseFloat(s.children[1].style.zoom), fits: s.scrollHeight <= s.clientHeight + 1,
                sameZoom: s.children[0].style.zoom === s.children[1].style.zoom};
    }""")
    assert fit['zoom'] < 1 and fit['fits'] and fit['sameZoom']

    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert page.evaluate("""() => !document.documentElement.classList.contains('print-layout')
        && [...document.querySelector('.slide').children].every(c => c.style.zoom === '')""")


def test_all_trees_fit_when_printing(reference):
    reference.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    trees = reference.evaluate("""() => [...document.querySelectorAll('.tree')].map(t => {
        const a = t.getBoundingClientRect(), b = t.firstElementChild.getBoundingClientRect();
        return {width: a.width, fits: b.left >= a.left - 0.5 && b.right <= a.right + 0.5};
    })""")
    assert len(trees) == 2
    assert all(t['width'] > 0 and t['fits'] for t in trees)


def test_short_slide_is_not_scaled(reference):
    reference.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    assert reference.evaluate("document.documentElement.classList.contains('print-layout')")
    assert reference.evaluate("document.querySelector('.slide').children[1].style.zoom") == ''
