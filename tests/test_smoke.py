"""以子行程實際執行 CLI 與啟動器，模擬繁體中文 Windows 的終端編碼（cp950）"""

import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def work_dir(tmp_path):
    """路徑含中文與空白的工作目錄"""
    path = tmp_path / '我的 簡報'
    path.mkdir()
    return path


def run(args, cwd, stdin='', stdout=subprocess.PIPE):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'cp950'
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd, env=env, input=stdin.encode('cp950'),
        stdout=stdout, stderr=subprocess.PIPE, timeout=60,
    )


def test_cli_build_with_output_redirected_to_file(work_dir):
    source = work_dir / '範例 投影片.md'
    shutil.copy(ROOT / 'examples' / 'example.md', source)
    output = work_dir / '輸出 結果.html'
    log = work_dir / '紀錄 檔.txt'

    with open(log, 'wb') as f:
        result = run(['-m', 'briefgen', 'build', '-i', str(source), '-o', str(output)],
                     cwd=work_dir, stdout=f)

    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
    assert output.exists()
    assert '已生成簡報' in log.read_bytes().decode('utf-8')


def launcher_env(work_dir):
    """家目錄、文件資料夾換成暫存資料夾；不開視窗、不開瀏覽器"""
    env = os.environ.copy()
    env.update(PYTHONIOENCODING='cp950', BROWSER='true', BRIEFGEN_NO_GUI='1',
               BRIEFGEN_HOME=str(work_dir / '家'), BRIEFGEN_DOCUMENTS=str(work_dir / '文件'))
    return env


def run_launcher(work_dir, answers, args=()):
    """執行啟動器；第一個回答給「已建立簡報資料夾」的按 Enter 繼續"""
    stdin = '\n'.join(['', *answers]) + '\n'
    result = subprocess.run([sys.executable, str(ROOT / 'launcher.py'), *args], cwd=work_dir,
                            env=launcher_env(work_dir), input=stdin.encode('cp950'),
                            capture_output=True, timeout=120)
    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
    return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')


def test_launcher_build_saves_html_next_to_markdown(work_dir):
    source = work_dir / '講義 資料夾' / '講義.md'
    source.parent.mkdir()
    shutil.copy(ROOT / 'examples' / 'template.md', source)
    # [1] 開啟 / 生成 -> [F] 輸入路徑 -> 回選單 -> [0] 結束
    out, _ = run_launcher(work_dir, ['1', 'F', str(source), '0', '0'])

    html = source.with_suffix('.html')
    assert f'[OK] 已生成：{html}' in out
    assert html.exists()
    assert list(work_dir.rglob('*_output.html')) == []
    config = json.loads((work_dir / '家' / '.briefgen' / 'launcher.json').read_text(encoding='utf-8'))
    assert config['recent'] == [str(source.resolve())]


def test_launcher_shows_fail_when_build_fails(work_dir):
    source = work_dir / '壞掉.md'
    source.write_bytes(b'# \xff\xfe')
    out, err = run_launcher(work_dir, ['1', 'F', str(source), '', '0'])
    assert '[FAIL] 生成失敗' in out and '[OK] 已生成' not in out
    assert 'UnicodeDecodeError' in err


def test_launcher_new_deck_structure(work_dir):
    out, _ = run_launcher(work_dir, ['3', '講義', 'n', '0'])
    folder = work_dir / '文件' / 'brief' / '講義'
    assert (folder / '講義.md').is_file() and (folder / 'images').is_dir()
    assert '[OK] 已建立：' in out


def test_launcher_generate_example_into_brief(work_dir):
    out, _ = run_launcher(work_dir, ['7', '0', '0'])
    folder = work_dir / '文件' / 'brief' / '範例'
    assert (folder / '範例.md').is_file() and (folder / 'images' / 'call-stack.svg').is_file()
    assert f'[OK] 已生成：{folder / "範例.html"}' in out
    assert '<title>遞迴</title>' in (folder / '範例.html').read_text(encoding='utf-8')  # 不覆寫標題


def test_launcher_migrate_makes_backup_and_warns_about_inline_tags(work_dir):
    source = work_dir / '舊講義.md'
    original = '# 舊\n<size<5>>大字\n<b>文字<color<red>>紅字\n'
    source.write_text(original, encoding='utf-8')
    out, _ = run_launcher(work_dir, ['4', 'F', str(source), '0', '4', 'F', str(source), '0', '0'])

    assert (work_dir / '舊講義.v2.bak.md').read_text(encoding='utf-8') == original
    assert (work_dir / '舊講義.v2.bak-2.md').is_file()  # 第二次轉換不覆蓋第一份備份
    assert source.read_text(encoding='utf-8').startswith('# 舊\n<size=5>大字\n')
    assert '行中間的 <color<red>>' in out and '[注意] 有 1 行在行中間寫了舊標籤' in out


def test_launcher_dropped_non_markdown_returns_to_menu(work_dir):
    txt = work_dir / '筆記.txt'
    txt.write_text('x', encoding='utf-8')
    out, _ = run_launcher(work_dir, ['', '0'], args=[str(txt)])
    assert '[FAIL] 只能選擇 .md 檔' in out and '[1] 開啟 / 生成簡報' in out


def test_start_bat_passes_dropped_files_to_launcher():
    assert '"%~dp0launcher.py" %*' in (ROOT / 'start.bat').read_text(encoding='ascii')


def _interactive(work_dir, args, stdin):
    launcher = subprocess.Popen(
        [sys.executable, str(ROOT / 'launcher.py'), *args], cwd=work_dir, env=launcher_env(work_dir),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    lines = queue.Queue()
    threading.Thread(target=lambda: [lines.put(l.decode('utf-8', 'replace')) for l in launcher.stdout],
                     daemon=True).start()
    launcher.stdin.write(stdin.encode('cp950'))
    launcher.stdin.flush()
    return launcher, lines


def _stop_preview_and_quit(launcher, lines):
    while '預覽網址' not in lines.get(timeout=30):
        pass
    os.killpg(launcher.pid, signal.SIGINT)  # 終端機的 Ctrl+C 會送給整個行程群組
    output = ''
    while '回到選單' not in output:
        output += lines.get(timeout=30)
    assert '[OK] 已結束即時預覽' in output
    # Enter 繼續 -> [0] 結束
    launcher.stdin.write(b'\n0\n')
    launcher.stdin.flush()
    assert launcher.wait(timeout=30) == 0


@pytest.mark.skipif(sys.platform == 'win32', reason='Windows 無法對子行程送出 Ctrl+C')
def test_launcher_live_preview_returns_to_menu_on_ctrl_c(work_dir):
    source = work_dir / '預覽 投影片.md'
    shutil.copy(ROOT / 'examples' / 'example.md', source)
    launcher, lines = _interactive(work_dir, [], f'\n2\nF\n{source}\n')
    try:
        _stop_preview_and_quit(launcher, lines)
        assert (work_dir / '預覽 投影片.html').exists()
    finally:
        if launcher.poll() is None:
            os.killpg(launcher.pid, signal.SIGKILL)


@pytest.mark.skipif(sys.platform == 'win32', reason='Windows 無法對子行程送出 Ctrl+C')
def test_launcher_dropped_markdown_starts_preview_without_menu(work_dir):
    source = work_dir / '拖進來的.md'
    shutil.copy(ROOT / 'examples' / 'template.md', source)
    launcher, lines = _interactive(work_dir, [str(source)], '\n')
    try:
        _stop_preview_and_quit(launcher, lines)
        assert source.with_suffix('.html').exists()
    finally:
        if launcher.poll() is None:
            os.killpg(launcher.pid, signal.SIGKILL)


def test_python_sources_are_cp950_encodable():
    """終端輸出的文字都寫在原始碼裡，必須能以 cp950 編碼"""
    sources = [ROOT / 'launcher.py', *(ROOT / 'src').rglob('*.py'), *(ROOT / 'tools').rglob('*.py')]
    bad = []
    for path in sources:
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            chars = {c for c in line if not c.isascii() and not _cp950_encodable(c)}
            if chars:
                bad.append(f'{path.relative_to(ROOT)}:{number}: {"".join(sorted(chars))}')
    assert bad == []


def _cp950_encodable(char):
    try:
        char.encode('cp950')
    except UnicodeEncodeError:
        return False
    return True
