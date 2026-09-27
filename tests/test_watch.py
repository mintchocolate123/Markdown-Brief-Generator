"""即時預覽（watch）：生成、失敗保留舊版、HTTP 路由、結束"""

import json
import os
import subprocess
import sys
import urllib.request

import pytest

from briefgen import watch
from briefgen.watch import STATUS_PATH, Watcher

DECK = '# 一\n第一張\n---\n# 二\n第二張\n'


def touch(path, text=None, data=None):
    """寫入並把修改時間往後推，確保輪詢看得到變動"""
    before = path.stat().st_mtime_ns if path.exists() else 0
    if data is not None:
        path.write_bytes(data)
    else:
        path.write_text(text, encoding='utf-8')
    later = max(path.stat().st_mtime_ns, before + 1_000_000_000)
    os.utime(path, ns=(later, later))


@pytest.fixture
def watcher(tmp_path):
    source = tmp_path / 'deck.md'
    touch(source, DECK)
    return Watcher(source, tmp_path / 'deck.html')


def test_build_writes_plain_html_and_serves_live_reload(watcher):
    assert watcher.check()
    written = watcher.output.read_text(encoding='utf-8')
    assert '第二張' in written
    for live_reload_marker in (STATUS_PATH, 'loadedVersion', 'briefgen-watch-status'):
        assert live_reload_marker not in written
    page = watcher.page()
    assert STATUS_PATH in page and 'const loadedVersion = 1;' in page
    assert page.index(STATUS_PATH) < page.rindex('</body>')
    assert watcher.status() == {'version': 1, 'error': None, 'warnings': []}


def test_unchanged_file_is_not_rebuilt(watcher):
    assert watcher.check()
    assert not watcher.check()
    assert watcher.status()['version'] == 1


def test_warnings_update_page_and_are_reported(watcher, capsys):
    watcher.check()
    touch(watcher.source, DECK + '<foo>錯字\n')
    assert watcher.check()
    status = watcher.status()
    assert status['version'] == 2 and status['error'] is None
    assert status['warnings'] == [f'{watcher.source}:6: 未知的格式名稱：foo，整行視為文字']
    assert '&lt;foo&gt;錯字' in watcher.page()
    assert '警告 1 則' in capsys.readouterr().out


def test_failure_keeps_previous_version(watcher, capsys):
    watcher.check()
    good = watcher.output.read_text(encoding='utf-8')
    touch(watcher.source, data=b'# \xff\xfe broken')
    assert watcher.check()
    status = watcher.status()
    assert status['version'] == 1
    assert status['error'].startswith('UnicodeDecodeError')
    assert '第二張' in watcher.page()
    assert watcher.output.read_text(encoding='utf-8') == good
    assert '[FAIL] 生成失敗：UnicodeDecodeError' in capsys.readouterr().err

    touch(watcher.source, DECK.replace('第二張', '修好了'))
    assert watcher.check()
    assert watcher.status() == {'version': 2, 'error': None, 'warnings': []}
    assert '修好了' in watcher.page()


def test_deleted_file_is_a_failure(watcher):
    watcher.check()
    watcher.source.unlink()
    assert watcher.check()
    assert watcher.status()['error'].startswith('FileNotFoundError')
    assert watcher.status()['version'] == 1


def test_page_before_first_successful_build(tmp_path):
    source = tmp_path / 'deck.md'
    source.write_bytes(b'\xff')
    w = Watcher(source, tmp_path / 'deck.html')
    w.check()
    assert '尚未成功生成' in w.page() and STATUS_PATH in w.page()
    assert not w.output.exists()


def test_http_routes(watcher):
    watcher.check()
    (watcher.source.parent / 'pic.txt').write_text('圖片', encoding='utf-8')
    server = watch.serve(watcher)
    base = f'http://127.0.0.1:{server.server_address[1]}'
    try:
        with urllib.request.urlopen(base + '/') as r:
            assert r.headers['Cache-Control'] == 'no-store'
            assert STATUS_PATH in r.read().decode('utf-8')
        with urllib.request.urlopen(base + STATUS_PATH) as r:
            assert json.loads(r.read().decode('utf-8')) == watcher.status()
        with urllib.request.urlopen(base + '/pic.txt') as r:
            assert r.read().decode('utf-8') == '圖片'
    finally:
        server.shutdown()
        server.server_close()


def test_ctrl_c_stops_cleanly(watcher, monkeypatch, capsys):
    def interrupt(_):
        raise KeyboardInterrupt
    monkeypatch.setattr(watch.time, 'sleep', interrupt)
    assert watch.run(watcher.source, watcher.output, open_browser=False) == 0
    out = capsys.readouterr().out
    assert '預覽網址：http://127.0.0.1:' in out and '[OK] 已結束即時預覽' in out


@pytest.mark.parametrize('name, message', [('deck.txt', '不支援的檔案格式'), ('missing.md', '找不到檔案')])
def test_cli_watch_rejects_bad_input(tmp_path, name, message):
    (tmp_path / 'deck.txt').write_text('x', encoding='utf-8')
    result = subprocess.run([sys.executable, '-m', 'briefgen', 'watch', name, '--no-open'],
                            cwd=tmp_path, capture_output=True, timeout=60)
    assert result.returncode == 1
    assert message in result.stderr.decode('utf-8')


def test_ctrl_c_while_opening_browser_stops_cleanly(watcher, monkeypatch, capsys):
    def interrupt(_):
        raise KeyboardInterrupt
    monkeypatch.setattr(watch.webbrowser, 'open', interrupt)
    assert watch.run(watcher.source, watcher.output) == 0
    assert '[OK] 已結束即時預覽' in capsys.readouterr().out
