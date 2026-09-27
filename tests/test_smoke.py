"""以子行程實際執行 CLI 與啟動器，模擬繁體中文 Windows 的終端編碼（cp950）"""

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
        cwd=cwd, env=env, input=stdin.encode('utf-8'),
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
