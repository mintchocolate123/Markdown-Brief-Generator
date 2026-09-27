"""上台操作：翻頁鍵、捲動、Home/End、全螢幕、黑屏、網址 hash"""

import pytest

from .helpers import open_slides

TALL_LINES = 120
DECK = '\n---\n'.join([
    '# 一\n第一張',
    '# 二\n第二張',
    '# 三（很長）\n' + '\n'.join(f'第 {n} 行' for n in range(1, TALL_LINES + 1)),
    '# 四\n第四張',
    '# 五\n第五張',
])


@pytest.fixture
def deck(page, build):
    html = build(DECK, name='deck')
    open_slides(page, html)
    page.html_path = html
    return page


def current(page):
    """目前頁數（1 起算），取自頁碼顯示"""
    return int(page.inner_text('#pageIndicator').split('/')[0])


def scroll_y(page):
    return page.evaluate('window.scrollY')


def at_bottom(page):
    return page.evaluate('window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 1')


def go(page, number):
    page.evaluate(f'showSlide({number - 1})')


@pytest.mark.parametrize('key', ['ArrowRight', 'ArrowDown', 'Space', 'PageDown'])
def test_next_keys(deck, key):
    deck.keyboard.press(key)
    assert current(deck) == 2


@pytest.mark.parametrize('key', ['ArrowLeft', 'ArrowUp', 'PageUp'])
def test_previous_keys(deck, key):
    go(deck, 2)
    deck.keyboard.press(key)
    assert current(deck) == 1


def test_first_and_last_slide_do_not_wrap(deck):
    deck.keyboard.press('ArrowLeft')
    assert current(deck) == 1
    deck.keyboard.press('End')
    deck.keyboard.press('PageDown')
    assert current(deck) == 5


def test_home_and_end(deck):
    deck.keyboard.press('End')
    assert current(deck) == 5
    deck.keyboard.press('Home')
    assert current(deck) == 1


@pytest.mark.parametrize('key', ['PageDown', 'ArrowDown', 'Space'])
def test_scroll_down_through_tall_slide_before_next(deck, key):
    go(deck, 3)
    presses = 0
    while not at_bottom(deck):
        before = scroll_y(deck)
        deck.keyboard.press(key)
        presses += 1
        assert current(deck) == 3
        assert scroll_y(deck) > before
        assert presses < 50
    assert presses >= 2
    deck.keyboard.press(key)
    assert current(deck) == 4
    assert scroll_y(deck) == 0


@pytest.mark.parametrize('key', ['PageUp', 'ArrowUp'])
def test_scroll_up_through_tall_slide_before_previous(deck, key):
    go(deck, 3)
    deck.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
    presses = 0
    while scroll_y(deck) > 1:
        deck.keyboard.press(key)
        presses += 1
        assert current(deck) == 3
        assert presses < 50
    assert presses >= 2
    deck.keyboard.press(key)
    assert current(deck) == 2
    assert scroll_y(deck) == 0


def test_scroll_step_keeps_overlap(deck):
    go(deck, 3)
    deck.keyboard.press('PageDown')
    visible = deck.evaluate("window.innerHeight - document.querySelector('.navigation').offsetHeight")
    assert 0 < scroll_y(deck) < visible


@pytest.mark.parametrize('key', ['ArrowRight', 'ArrowLeft'])
def test_left_right_change_slide_even_when_scrolled(deck, key):
    go(deck, 3)
    deck.keyboard.press('PageDown')
    deck.keyboard.press(key)
    assert current(deck) == (4 if key == 'ArrowRight' else 2)
    assert scroll_y(deck) == 0


def test_space_on_focused_button_advances_once(deck):
    deck.click('#nextBtn')
    assert current(deck) == 2
    deck.keyboard.press('Space')
    assert current(deck) == 3


def test_blackout_toggle_and_resume_without_moving(deck):
    go(deck, 2)
    blackout = deck.locator('#blackout')
    deck.keyboard.press('b')
    assert blackout.is_visible()
    deck.keyboard.press('ArrowRight')
    assert not blackout.is_visible()
    assert current(deck) == 2
    deck.keyboard.press('B')
    assert blackout.is_visible()
    deck.keyboard.press('b')
    assert not blackout.is_visible()
    assert current(deck) == 2


def test_fullscreen_toggle(deck):
    deck.keyboard.press('f')
    deck.wait_for_function('document.fullscreenElement === document.documentElement')
    deck.keyboard.press('F')
    deck.wait_for_function('document.fullscreenElement === null')


def test_modifier_keys_are_ignored(deck):
    deck.keyboard.press('Control+f')
    deck.keyboard.press('Control+ArrowRight')
    assert deck.evaluate('document.fullscreenElement') is None
    assert current(deck) == 1


def test_hash_follows_current_slide_without_history_entries(deck):
    length = deck.evaluate('history.length')
    deck.keyboard.press('ArrowRight')
    deck.keyboard.press('ArrowRight')
    assert deck.evaluate('location.hash') == '#3'
    assert deck.evaluate('history.length') == length


def test_open_with_hash_and_reload(deck):
    deck.goto(deck.html_path.as_uri() + '#4')
    assert current(deck) == 4
    deck.keyboard.press('ArrowLeft')
    deck.reload()
    assert current(deck) == 3


@pytest.mark.parametrize('hash_', ['#0', '#6', '#abc', ''])
def test_invalid_hash_opens_first_slide(deck, hash_):
    deck.goto(deck.html_path.as_uri() + hash_)
    assert current(deck) == 1


def test_editing_hash_jumps_to_slide(deck):
    deck.evaluate("location.hash = '#5'")
    deck.wait_for_function("document.getElementById('pageIndicator').textContent.startsWith('5')")
    assert current(deck) == 5
