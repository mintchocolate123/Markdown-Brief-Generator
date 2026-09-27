"""生成結果必須與 tests/golden/ 逐字相同"""

from pathlib import Path

import pytest

from briefgen.generator import PresentationGenerator

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / 'tests' / 'golden'

FIXTURE_DIR = ROOT / 'tests' / 'fixtures' / 'new'
CASES = ['example', '格式參考', 'edge_cases']

# 每份 fixture 預期的警告（fixture 內的行號與訊息），其他警告都不允許
EXPECTED_WARNINGS = {
    'example': [],
    '格式參考': [],
    'edge_cases': [
        (34, '段落第一行的 cont 沒有可接續的行，當作一般行'),
        (39, '段落第一行的 cont 沒有可接續的行，當作一般行'),
        (53, '表格儲存格不支援 cont，已忽略'),
        (129, '清單項目不支援 pivot，已忽略'),
    ],
}


@pytest.mark.parametrize('name', CASES)
def test_matches_golden(name, tmp_path, capsys):
    gen = PresentationGenerator()
    source = FIXTURE_DIR / f'{name}.md'
    gen.load_from_markdown(str(source))
    gen.presentation.title = '簡報'
    output = tmp_path / f'{name}.html'
    gen.generate_html(str(output))

    expected = (GOLDEN_DIR / f'{name}.html').read_text(encoding='utf-8')
    assert output.read_text(encoding='utf-8') == expected
    expected_warnings = [f'{source}:{line}: {message}' for line, message in EXPECTED_WARNINGS[name]]
    assert capsys.readouterr().err.splitlines() == expected_warnings
