"""生成結果必須與 tests/golden/ 逐字相同"""

from pathlib import Path

import pytest

from briefgen.generator import PresentationGenerator

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / 'tests' / 'golden'

FIXTURE_DIR = ROOT / 'tests' / 'fixtures' / 'new'
CASES = ['example', '格式參考', 'edge_cases']


@pytest.mark.parametrize('name', CASES)
def test_matches_golden(name, tmp_path, capsys):
    gen = PresentationGenerator()
    gen.load_from_markdown(str(FIXTURE_DIR / f'{name}.md'))
    gen.presentation.title = '簡報'
    output = tmp_path / f'{name}.html'
    gen.generate_html(str(output))

    expected = (GOLDEN_DIR / f'{name}.html').read_text(encoding='utf-8')
    assert output.read_text(encoding='utf-8') == expected
    assert capsys.readouterr().err == ''
