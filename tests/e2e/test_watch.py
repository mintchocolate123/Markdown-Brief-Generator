"""即時預覽：存檔後瀏覽器自動重新載入並停在同一張；失敗保留舊版並顯示提示"""

import os
import queue
import signal
import subprocess
import sys
import threading

import pytest

DECK = '# 一\n第一張\n---\n# 二\n第二張：{}\n---\n# 三\n第三張\n'


def touch(path, text=None, data=None):
    before = path.stat().st_mtime_ns if path.exists() else 0
    if data is not None:
        path.write_bytes(data)
    else:
        path.write_text(text, encoding='utf-8')
    later = max(path.stat().st_mtime_ns, before + 1_000_000_000)
    os.utime(path, ns=(later, later))


class WatchProcess:
    """在子行程執行 briefgen watch，逐行收集輸出"""

    def __init__(self, source):
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        self.process = subprocess.Popen(
            [sys.executable, '-m', 'briefgen', 'watch', str(source), '--no-open'],
            cwd=source.parent, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags)
        self.lines = queue.Queue()
        self.output = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self.process.stdout:
            self.lines.put(raw.decode('utf-8').rstrip('\r\n'))

    def wait_for(self, text, timeout=20):
        while True:
            line = self.lines.get(timeout=timeout)
            self.output.append(line)
            if text in line:
                return line

    def stop(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=20)


@pytest.fixture
def watching(tmp_path):
    source = tmp_path / '預覽 投影片.md'
    touch(source, DECK.format('初版'))
    proc = WatchProcess(source)
    url = proc.wait_for('預覽網址：').split('：', 1)[1]
    proc.source, proc.url = source, url
    yield proc
    proc.stop()


def current(page):
    return int(page.inner_text('#pageIndicator').split('/')[0])


def test_reload_on_save_stays_on_slide(page, watching):
    page.goto(watching.url + '#2')
    assert '初版' in page.inner_text('.slide.active')

    touch(watching.source, DECK.format('第二版'))
    page.wait_for_function("document.querySelector('.slide.active')?.innerText.includes('第二版')")
    assert current(page) == 2
    assert page.locator('#briefgen-watch-status').is_hidden()


def test_failure_keeps_previous_version_and_shows_error(page, watching):
    page.goto(watching.url + '#2')
    touch(watching.source, data=b'# \xff\xfe')
    watching.wait_for('[FAIL] 生成失敗')
    status = page.locator('#briefgen-watch-status')
    status.wait_for(state='visible')
    assert 'UnicodeDecodeError' in status.inner_text()
    assert '初版' in page.inner_text('.slide.active')

    touch(watching.source, DECK.format('修好了'))
    page.wait_for_function("document.querySelector('.slide.active')?.innerText.includes('修好了')")
    assert current(page) == 2
    assert page.locator('#briefgen-watch-status').is_hidden()


def test_warnings_update_page_and_are_listed(page, watching):
    page.goto(watching.url + '#3')
    touch(watching.source, DECK.format('初版') + '<foo>錯字\n')
    page.wait_for_function("document.querySelector('.slide.active')?.innerText.includes('<foo>錯字')")
    status = page.locator('#briefgen-watch-status')
    status.wait_for(state='visible')
    assert f'{watching.source}:9: 未知的格式名稱：foo' in status.inner_text()
    assert current(page) == 3


def test_written_html_has_no_live_reload(page, watching):
    page.goto(watching.url)
    written = watching.source.with_suffix('.html').read_text(encoding='utf-8')
    assert '第二張' in written
    assert 'loadedVersion' not in written and '__briefgen' not in written
    assert page.locator('#briefgen-watch-status').count() == 1


@pytest.mark.skipif(sys.platform == 'win32', reason='Windows 無法對子行程送出 Ctrl+C；結束流程由 test_watch.py 以 KeyboardInterrupt 驗證')
def test_ctrl_c_exits_cleanly(watching):
    watching.process.send_signal(signal.SIGINT)
    assert watching.process.wait(timeout=20) == 0
    watching.wait_for('[OK] 已結束即時預覽')
