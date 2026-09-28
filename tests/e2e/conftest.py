"""
瀏覽器端測試的共用 fixture

沒有 playwright 或 chromium 時整組 skip；設定 BRIEFGEN_REQUIRE_E2E=1（CI）時改為失敗。
"""

import os
from pathlib import Path

import pytest

from briefgen.generator import PresentationGenerator


def _unavailable(reason):
    if os.environ.get('BRIEFGEN_REQUIRE_E2E') == '1':
        pytest.fail(reason)
    pytest.skip(reason)


def pytest_terminal_summary(terminalreporter):
    """測試結束後印出 GitHub Actions 的 notice；直接寫 UTF-8，避免 Windows 終端編碼把中文跳脫"""
    import sys
    from .helpers import GITHUB_NOTICES
    # 先換行：pytest 的進度點可能還在同一行，workflow 指令必須在行首才會被辨識
    for notice in GITHUB_NOTICES:
        sys.stdout.buffer.write(('\n' + notice + '\n').encode('utf-8'))
    sys.stdout.flush()


@pytest.fixture(scope='session')
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _unavailable('未安裝 playwright')
    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.launch()
    except Exception as error:  # 瀏覽器未安裝等
        playwright.stop()
        _unavailable(f'無法啟動 chromium：{str(error).splitlines()[0]}')
    yield browser
    browser.close()
    playwright.stop()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def build(tmp_path):
    """把 Markdown 檔（路徑）或內容（字串）生成為 HTML，回傳 HTML 路徑"""
    def _build(source, name='slides'):
        if isinstance(source, Path):
            markdown = source
        else:
            markdown = tmp_path / f'{name}.md'
            markdown.write_text(source, encoding='utf-8')
        output = tmp_path / f'{name}.html'
        gen = PresentationGenerator()
        gen.load_from_markdown(str(markdown))
        gen.generate_html(str(output))
        return output
    return _build

