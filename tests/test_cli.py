"""命令列：--title 與錯誤結束碼"""

import json
import re
import subprocess
import sys

import pytest

MARKDOWN = '# 第一張\n內容\n'


def briefgen(*args, cwd):
    result = subprocess.run([sys.executable, '-m', 'briefgen', *args], cwd=cwd,
                            capture_output=True, timeout=60)
    return result.returncode, result.stdout.decode('utf-8'), result.stderr.decode('utf-8')


def html_title(path):
    return re.search(r'<title>(.*)</title>', path.read_text(encoding='utf-8')).group(1)


@pytest.fixture
def files(tmp_path):
    (tmp_path / 'a.md').write_text(MARKDOWN, encoding='utf-8')
    (tmp_path / 'p.json').write_text(json.dumps({'title': 'JSON 標題', 'slides': [{'title': 'x'}]}),
                                     encoding='utf-8')
    return tmp_path


@pytest.mark.parametrize('source, title_args, expected', [
    ('a.md', [], '簡報'),
    ('a.md', ['-t', '指定標題'], '指定標題'),
    ('p.json', [], 'JSON 標題'),
    ('p.json', ['-t', '指定標題'], '指定標題'),
])
def test_build_title(files, source, title_args, expected):
    code, _, _ = briefgen('build', '-i', source, '-o', 'out.html', *title_args, cwd=files)
    assert code == 0
    assert html_title(files / 'out.html') == expected


def test_new_uses_default_title_without_option(tmp_path):
    assert briefgen('new', '-o', 'p.json', cwd=tmp_path)[0] == 0
    assert json.loads((tmp_path / 'p.json').read_text(encoding='utf-8'))['title'] == '簡報'


@pytest.mark.parametrize('args, message', [
    (['build'], '請指定輸入檔案 (-i)'),
    (['build', '-i', 'a.txt'], '不支援的檔案格式'),
    (['export-slides'], '請指定輸入檔案 (-i)'),
    (['export-slides', '-i', 'a.txt'], '不支援的檔案格式'),
])
def test_errors_go_to_stderr_with_nonzero_exit(tmp_path, args, message):
    code, out, err = briefgen(*args, cwd=tmp_path)
    assert code == 1
    assert out == ''
    assert err.startswith('[FAIL] 錯誤：') and message in err
