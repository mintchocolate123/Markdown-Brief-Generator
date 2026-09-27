"""瀏覽器端測試的輔助函式"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 測試結束後才印出的 GitHub Actions 訊息（測試執行中 stdout 會被 pytest 擷取）
GITHUB_NOTICES = []


def open_slides(page, html):
    """開啟簡報並關閉淡入動畫"""
    page.goto(html.as_uri())
    page.add_style_tag(content='.slide { animation: none !important; }')


def show_slide_titled(page, title):
    """切換到指定標題的投影片，回傳索引"""
    index = page.evaluate("""t => [...document.querySelectorAll('.slide')]
        .findIndex(s => s.querySelector('h1')?.textContent === t)""", title)
    assert index >= 0, title
    page.evaluate(f'currentIndex = {index}; showSlide({index})')
    return index
