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
