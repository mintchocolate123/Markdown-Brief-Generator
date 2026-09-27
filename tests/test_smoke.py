"""以子行程實際執行 CLI 與啟動器，模擬繁體中文 Windows 的終端編碼（cp950）"""

import importlib.util
import os
import shutil
import subprocess
import sys
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


def test_launcher_generate_example(work_dir):
    # [2] 生成範例 -> 不開啟 -> Enter 繼續 -> [0] 結束
    result = run([str(ROOT / 'launcher.py')], cwd=work_dir, stdin='2\nn\n\n0\n')

    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
    assert (work_dir / 'example_output.html').exists()
    assert '完成' in result.stdout.decode('utf-8')


def test_launcher_shows_fail_when_build_fails(work_dir):
    source = work_dir / '不支援 格式.txt'
    source.write_text('文字', encoding='utf-8')
    # [1] 從 Markdown 生成 -> 檔案路徑 -> 預設輸出 -> Enter 繼續 -> [0] 結束
    result = run([str(ROOT / 'launcher.py')], cwd=work_dir, stdin=f'1\n{source}\n\n\n0\n')

    assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
    stdout = result.stdout.decode('utf-8')
    assert '[FAIL] 失敗' in stdout
    assert '[OK]' not in stdout
    assert '不支援的檔案格式' in result.stderr.decode('utf-8')


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


def test_launcher_open_file_uses_file_uri(work_dir, monkeypatch):
    spec = importlib.util.spec_from_file_location('launcher', ROOT / 'launcher.py')
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    opened = []
    monkeypatch.setattr(launcher.webbrowser, 'open', opened.append)
    monkeypatch.chdir(work_dir)

    launcher.open_file('輸出 結果.html')

    assert opened == [(work_dir / '輸出 結果.html').as_uri()]
    assert opened[0].startswith('file:///') and '%20' in opened[0]
