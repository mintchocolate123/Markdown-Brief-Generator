"""文件與範例必須能無警告地生成"""

from pathlib import Path

import pytest

from briefgen.generator import PresentationGenerator

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize('path', ['docs/格式參考.md', 'examples/example.md'])
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
    files = [ROOT / 'README.md', *(ROOT / 'docs').rglob('*.md'), *(ROOT / 'examples').rglob('*.md')]
    found = []
    for path in files:
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
