"""文件與範例：能無警告生成、連結有效、指令能執行、沒有 emoji、語法速查與程式一致"""

import os
import queue
import re
import shlex
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import unquote

import pytest

from briefgen.generator import PresentationGenerator
from briefgen.highlighter import SyntaxHighlighter
from briefgen.parsing.blocks import MarkdownParser
from briefgen.tags import COLOR_MAP, FLAG_FORMATS, VALUE_FORMATS

ROOT = Path(__file__).resolve().parent.parent
SLIDE_SOURCES = sorted([*(ROOT / 'docs').rglob('*.md'), *(ROOT / 'examples').rglob('*.md')])
DOCUMENTS = [ROOT / 'README.md', ROOT / 'CHANGELOG.md', ROOT / 'CLAUDE.md', *SLIDE_SOURCES]


def relative(path):
    return str(path.relative_to(ROOT))


@pytest.mark.parametrize('path', [relative(p) for p in SLIDE_SOURCES])
def test_builds_without_warnings(path, tmp_path, capsys):
    gen = PresentationGenerator()
    gen.load_from_markdown(str(ROOT / path))
    gen.generate_html(str(tmp_path / 'out.html'))
    assert capsys.readouterr().err == ''


# Unicode emoji：補充平面的 emoji 區段、基本平面中預設以 emoji 顯示的字元（Emoji_Presentation），
# 以及把一般字元變成 emoji 的變體選擇符 U+FE0F
EMOJI_RANGES = [
    (0x1F000, 0x1FAFF),
    (0x231A, 0x231B), (0x23E9, 0x23EC), (0x23F0, 0x23F0), (0x23F3, 0x23F3),
    (0x25FD, 0x25FE), (0x2614, 0x2615), (0x2648, 0x2653), (0x267F, 0x267F),
    (0x2693, 0x2693), (0x26A1, 0x26A1), (0x26AA, 0x26AB), (0x26BD, 0x26BE),
    (0x26C4, 0x26C5), (0x26CE, 0x26CE), (0x26D4, 0x26D4), (0x26EA, 0x26EA),
    (0x26F2, 0x26F3), (0x26F5, 0x26F5), (0x26FA, 0x26FA), (0x26FD, 0x26FD),
    (0x2705, 0x2705), (0x270A, 0x270B), (0x2728, 0x2728), (0x274C, 0x274C),
    (0x274E, 0x274E), (0x2753, 0x2755), (0x2757, 0x2757), (0x2795, 0x2797),
    (0x27B0, 0x27B0), (0x27BF, 0x27BF), (0x2B1B, 0x2B1C), (0x2B50, 0x2B50),
    (0x2B55, 0x2B55), (0xFE0F, 0xFE0F),
]


def _is_emoji(char):
    return any(low <= ord(char) <= high for low, high in EMOJI_RANGES)


def test_no_emoji_in_docs_examples_and_readme():
    found = []
    for path in DOCUMENTS:
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            chars = [f'U+{ord(c):04X}' for c in line if _is_emoji(c)]
            if chars:
                found.append(f'{path.relative_to(ROOT)}:{number}: {" ".join(chars)}')
    assert found == []


@pytest.mark.parametrize('text, expected', [
    ('\U0001F389', True), ('⏳', True), ('⭐', True), ('❤️', True),
    ('✓', False), ('★☆', False), ('△', False), ('ヽ(・∀・)ノ', False),
])
def test_emoji_detection(text, expected):
    assert any(_is_emoji(c) for c in text) is expected



# --- 相對連結 -----------------------------------------------------------------

LINK_RE = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')


def _anchor(heading):
    """GitHub 標題錨點：小寫，去掉標點，空白換成 -"""
    return re.sub(r'[^\w\- ]', '', heading.strip().lower()).replace(' ', '-')


def _anchors(path):
    text = path.read_text(encoding='utf-8')
    return {_anchor(m.group(1)) for m in re.finditer(r'^#+\s+(.+)$', text, re.M)}


def test_relative_links_point_to_existing_files():
    broken = []
    for doc in DOCUMENTS:
        for number, line in enumerate(doc.read_text(encoding='utf-8').splitlines(), 1):
            for target in LINK_RE.findall(line):
                if re.match(r'[a-z]+:', target) or target.startswith('#'):
                    continue
                file_part, _, anchor = unquote(target).partition('#')
                resolved = (doc.parent / file_part).resolve()
                if not resolved.exists():
                    broken.append(f'{relative(doc)}:{number}: {target}')
                elif anchor and anchor not in _anchors(resolved):
                    broken.append(f'{relative(doc)}:{number}: {target}（找不到標題）')
    assert broken == []


# --- 文件中的指令 --------------------------------------------------------------

COMMAND_PREFIXES = ('briefgen ', 'python -m briefgen ', 'python tools/migrate_syntax.py ')


def _documented_commands():
    """README 與 docs/ 裡 bash 程式碼區塊中的 briefgen / migrate_syntax 指令"""
    commands = []
    for doc in [ROOT / 'README.md', *sorted((ROOT / 'docs').rglob('*.md'))]:
        in_bash = False
        for number, line in enumerate(doc.read_text(encoding='utf-8').splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith('```'):
                in_bash = not in_bash and stripped == '```bash'
                continue
            if in_bash and stripped.startswith(COMMAND_PREFIXES):
                commands.append((f'{relative(doc)}:{number}', stripped))
    return commands


def _prepare(workdir, argv):
    """在暫存資料夾準備指令用到、但還不存在的 .md 檔"""
    migrate = 'migrate_syntax.py' in ' '.join(argv)
    sample = ROOT / ('tests/fixtures/old/example.md' if migrate else 'examples/template.md')
    for arg in argv:
        if arg.endswith('.md'):
            path = workdir / arg
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(sample, path)


def _run_watch(argv, workdir):
    process = subprocess.Popen(argv + ['--no-open'], cwd=workdir, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    lines = queue.Queue()
    threading.Thread(target=lambda: [lines.put(l.decode('utf-8', 'replace')) for l in process.stdout],
                     daemon=True).start()
    output = ''
    try:
        while '預覽網址' not in output:
            output += lines.get(timeout=30)
    finally:
        process.kill()
        process.wait(timeout=30)
    return output


def test_documented_commands_run(tmp_path):
    commands = _documented_commands()
    assert len(commands) >= 6
    for name in ('docs', 'examples', 'tools'):
        shutil.copytree(ROOT / name, tmp_path / name)
    env = os.environ.copy()
    env['HOME'] = str(tmp_path)
    for location, command in commands:
        argv = shlex.split(os.path.expandvars(command.replace('$HOME', str(tmp_path))))
        argv = [sys.executable, '-m', 'briefgen', *argv[1:]] if argv[0] == 'briefgen' else [sys.executable, *argv[1:]]
        _prepare(tmp_path, argv)
        if 'watch' in argv:
            assert '預覽網址' in _run_watch(argv, tmp_path), location
            continue
        result = subprocess.run(argv, cwd=tmp_path, capture_output=True, env=env, timeout=60)
        assert result.returncode == 0, f'{location}: {command}\n{result.stderr.decode("utf-8", "replace")}'
        if '-o' in argv:
            assert (tmp_path / argv[argv.index('-o') + 1]).exists(), location


# --- 語法速查與程式一致 -----------------------------------------------------------

CHEATSHEET = ROOT / 'docs' / '語法速查.md'


def test_cheatsheet_lists_every_format_name():
    text = CHEATSHEET.read_text(encoding='utf-8')
    # 名稱出現在反引號內，前後不是英數字或 -（例如 `<cont b>`、`size=5`）
    missing = [name for name in [*FLAG_FORMATS, *VALUE_FORMATS]
               if not re.search(r'`[^`\n]*(?<![\w-])' + re.escape(name) + r'(?![\w-])[^`\n]*`', text)]
    assert missing == []


def test_cheatsheet_and_spec_list_every_color():
    cheatsheet = CHEATSHEET.read_text(encoding='utf-8')
    spec = (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
    missing = [f'{name} {code}' for name, code in COLOR_MAP.items()
               if f'`{name}` | `{code}`' not in cheatsheet]
    assert missing == []
    changed = {n: c for n, c in COLOR_MAP.items() if n in ('red', 'green', 'blue', 'purple', 'gray')}
    assert all(f'{name} {code}' in spec for name, code in changed.items())


def test_cheatsheet_lists_every_code_language():
    text = CHEATSHEET.read_text(encoding='utf-8')
    languages = [*SyntaxHighlighter.LANG_COLORS, *MarkdownParser.LANG_NORMALIZE]
    assert [lang for lang in languages if f'`{lang}`' not in text] == []
