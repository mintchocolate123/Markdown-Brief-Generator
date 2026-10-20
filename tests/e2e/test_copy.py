"""程式碼區塊的「複製」按鈕：Clipboard API、退回 execCommand、都失敗時選取程式碼、相同內容的區塊"""

import pytest

from .helpers import ROOT, open_slides, show_slide_titled

CODE = '''def 問候(name):
    if name < 3 and name > 0 & True:
        return "<b>你好</b>"

    return '單引號' + "雙引號"'''

DECK = f'''# 複製
## 特殊字元

```py
{CODE}
```

---

# 相同內容
## 兩段一樣的程式碼

```py
print(1)
```

```py
print(1)
```
'''

NO_CLIPBOARD = "Object.defineProperty(navigator, 'clipboard', {value: undefined, configurable: true});"
NO_EXEC_COMMAND = "document.execCommand = () => false;"


@pytest.fixture
def context(browser):
    context = browser.new_context(viewport={'width': 1280, 'height': 720},
                                  permissions=['clipboard-read', 'clipboard-write'])
    yield context
    context.close()


@pytest.fixture
def deck(build):
    return build(DECK, name='copy')


def open_deck(context, html, *init_scripts):
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    for script in init_scripts:
        page.add_init_script(script)
    open_slides(page, html)
    page.errors = errors
    return page


def clipboard_text(context, html):
    """用另一個沒有被修改的頁面讀剪貼簿（file:// 是安全環境，about:blank 沒有 Clipboard API）

    Windows 的剪貼簿把換行存成 CRLF（作業系統的慣例，程式本身放進剪貼簿的是 LF），
    所以比對前統一成 LF。只換 CRLF，單獨出現的 CR 會留著讓測試失敗。
    """
    reader = context.new_page()
    reader.goto(html.as_uri())
    try:
        text = reader.evaluate('navigator.clipboard.readText()')
    finally:
        reader.close()
    return text.replace('\r\n', '\n')


def test_clipboard_api_copies_exact_code(context, deck):
    page = open_deck(context, deck)
    page.click('#copyBtn1')
    page.wait_for_function("document.getElementById('copyBtn1').textContent === '已複製'")
    assert clipboard_text(context, deck) == CODE
    assert page.errors == []


def test_falls_back_when_clipboard_api_is_missing(context, deck):
    page = open_deck(context, deck, NO_CLIPBOARD)
    assert page.evaluate('navigator.clipboard') is None
    page.click('#copyBtn1')
    page.wait_for_function("document.getElementById('copyBtn1').textContent === '已複製'")
    assert clipboard_text(context, deck) == CODE
    assert page.errors == []


def test_falls_back_when_write_text_throws(context, deck):
    page = open_deck(context, deck,
                     "navigator.clipboard.writeText = () => { throw new Error('blocked'); };")
    page.click('#copyBtn1')
    page.wait_for_function("document.getElementById('copyBtn1').textContent === '已複製'")
    assert clipboard_text(context, deck) == CODE


def test_falls_back_when_write_text_rejects(context, deck):
    page = open_deck(context, deck,
                     "navigator.clipboard.writeText = () => Promise.reject(new Error('denied'));")
    page.click('#copyBtn1')
    page.wait_for_function("document.getElementById('copyBtn1').textContent === '已複製'")
    assert clipboard_text(context, deck) == CODE


@pytest.mark.parametrize('broken_exec', [NO_EXEC_COMMAND, "document.execCommand = () => { throw new Error('x'); };"])
def test_both_methods_fail_shows_failure_and_selects_code(context, deck, broken_exec):
    page = open_deck(context, deck, NO_CLIPBOARD, broken_exec)
    page.click('#copyBtn1')
    page.wait_for_function("document.getElementById('copyBtn1').textContent === '複製失敗'")
    assert page.evaluate('window.getSelection().toString()') == CODE
    assert page.errors == []
    # 2 秒後恢復成「複製」
    page.wait_for_function("document.getElementById('copyBtn1').textContent === '複製'", timeout=5000)


def test_identical_blocks_copy_and_report_separately(context, deck):
    page = open_deck(context, deck)
    show_slide_titled(page, '相同內容')
    assert page.evaluate("[...document.querySelectorAll('.slide.active button')].map(b => b.id)") == \
        ['copyBtn2', 'copyBtn3']
    page.click('#copyBtn3')
    page.wait_for_function("document.getElementById('copyBtn3').textContent === '已複製'")
    assert page.inner_text('#copyBtn2') == '複製'
    assert clipboard_text(context, deck) == 'print(1)'


def test_ids_are_unique_across_the_whole_deck(context, build):
    page = open_deck(context, build(ROOT / 'docs' / '格式參考.md'))
    ids = page.evaluate("[...document.querySelectorAll('button[id^=copyBtn]')].map(b => b.id)")
    assert len(ids) == len(set(ids)) > 1


def test_buttons_are_not_covered_and_do_not_change_slide(context, build):
    """每個複製按鈕的中心點都點得到按鈕本身（沒有被導覽列、遮罩等擋住），點了不會換頁"""
    page = open_deck(context, build(ROOT / 'docs' / '格式參考.md'))
    page.keyboard.press('b')
    page.keyboard.press('b')  # 黑屏開關一次，確認關掉後不再擋住
    slides = page.evaluate("""() => [...document.querySelectorAll('.slide')]
        .map((s, i) => s.querySelector('button[id^=copyBtn]') ? i : -1).filter(i => i >= 0)""")
    assert len(slides) >= 5
    for index in slides:
        page.evaluate(f'showSlide({index})')
        covered = page.evaluate("""() => [...document.querySelectorAll('.slide.active button[id^=copyBtn]')]
            .filter(b => { const r = b.getBoundingClientRect();
                           return document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2) !== b; })
            .map(b => b.id)""")
        assert covered == [], f'第 {index + 1} 頁'
        button = page.locator('.slide.active button[id^=copyBtn]').first
        button.click()
        assert page.evaluate('currentIndex') == index
