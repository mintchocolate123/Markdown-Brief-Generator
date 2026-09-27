"""圖片：生成的 HTML 搬到別的資料夾後，本機圖片仍能顯示"""

import shutil

from .helpers import ROOT, open_slides, show_slide_titled

LOADED = """() => [...document.querySelectorAll('.slide.active img')]
    .map(img => ({complete: img.complete, width: img.naturalWidth, shown: img.getBoundingClientRect().width}))"""


def test_copied_html_still_shows_local_images(page, build, tmp_path):
    html = build(ROOT / 'docs' / '格式參考.md')
    moved = tmp_path / '搬走 的資料夾' / '格式參考.html'
    moved.parent.mkdir()
    shutil.copy(html, moved)

    open_slides(page, moved)
    show_slide_titled(page, '圖片')
    images = page.evaluate(LOADED)
    assert len(images) == 2
    assert all(i['complete'] and i['width'] == 400 for i in images)
    assert [round(i['shown']) for i in images] == [400, 200]


def test_image_shrinks_proportionally_in_narrow_window(page, build):
    open_slides(page, build(ROOT / 'docs' / '格式參考.md'))
    page.set_viewport_size({'width': 380, 'height': 800})
    show_slide_titled(page, '圖片')
    box = page.evaluate("document.querySelector('.slide.active img').getBoundingClientRect().toJSON()")
    assert box['width'] < 400
    assert abs(box['width'] / box['height'] - 2) < 0.02


GREEN = (0, 255, 0)


def green_box(page, selector):
    """元素截圖中純綠色像素的範圍（寬, 高）"""
    from io import BytesIO
    from PIL import Image
    image = Image.open(BytesIO(page.locator(selector).screenshot())).convert('RGB')
    xs, ys = [], []
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = image.getpixel((x, y))
            if g > 200 and r < 60 and b < 60:
                xs.append(x)
                ys.append(y)
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def solid_svg(path, width, height):
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                    f'<rect width="{width}" height="{height}" fill="#00ff00"/></svg>', encoding='utf-8')


def test_different_ratio_is_contained_not_stretched(page, build, tmp_path):
    solid_svg(tmp_path / 'square.svg', 100, 100)
    open_slides(page, build('# 圖\n<img=square.svg,400,200>', name='ratio'))
    box = page.evaluate("document.querySelector('.slide.active img').getBoundingClientRect().toJSON()")
    assert (round(box['width']), round(box['height'])) == (400, 200)
    width, height = green_box(page, '.slide.active img')
    assert abs(width - 200) <= 2 and abs(height - 200) <= 2  # 正方形完整顯示在框內


def test_height_only_keeps_ratio_when_width_is_capped(page, build, tmp_path):
    solid_svg(tmp_path / 'wide.svg', 400, 100)
    open_slides(page, build('# 圖\n<img=wide.svg,auto,200>', name='capped'))
    page.set_viewport_size({'width': 380, 'height': 800})
    card = page.evaluate("document.querySelector('.slide.active .slide-content').clientWidth")
    box = page.evaluate("document.querySelector('.slide.active img').getBoundingClientRect().toJSON()")
    assert box['width'] < 800 and round(box['height']) == 200  # 寬度被 max-width 壓縮，高度維持
    width, height = green_box(page, '.slide.active img')
    assert abs(width / height - 4) < 0.1  # 原圖 4:1 沒有被壓扁
    assert card > 0
