"""圖片：寬高、本機圖片嵌入、找不到時的警告"""

import base64
import subprocess
import sys

import pytest

from briefgen.generator import PresentationGenerator
from briefgen.model import Slide
from briefgen.render.html import HTMLRenderer

PNG = base64.b64decode(  # 1x1 透明 PNG
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')


def render(content, base_dir=None):
    warnings = []
    renderer = HTMLRenderer(warn=lambda s, line, msg: warnings.append((line + 1, msg)), base_dir=base_dir)
    html = renderer.render_slide(Slide(content=content), 0)
    body = html[len('<div class="slide" id="slide1"><div class="slide-content">'):-len('</div></div>')]
    return body, warnings


@pytest.mark.parametrize('size, style', [
    ('400,200', 'width:400px;aspect-ratio:400/200;height:auto;object-fit:contain;max-width:100%;border-radius:10px;'),
    ('400,auto', 'width:400px;max-width:100%;border-radius:10px;'),
    ('auto,200', 'height:200px;object-fit:contain;max-width:100%;border-radius:10px;'),
    ('auto,auto', 'max-width:100%;border-radius:10px;'),
])
def test_size_styles(size, style):
    assert render(f'<img=https://a.com/a.png,{size}>')[0] == f'<div><img src="https://a.com/a.png" style="{style}"></div>'


@pytest.mark.parametrize('url', ['https://a.com/a.png', 'http://a.com/a.png', 'HTTPS://A.COM/A.PNG'])
def test_web_urls_are_kept(url, tmp_path):
    body, warnings = render(f'<img={url},auto,auto>', base_dir=tmp_path)
    assert f'src="{url}"' in body and warnings == []


def test_url_is_html_escaped():
    body, _ = render('<img=https://a.com/?a=1&b="2",auto,auto>')
    assert 'src="https://a.com/?a=1&amp;b=&quot;2&quot;"' in body


@pytest.mark.parametrize('name, mime', [('p.png', 'image/png'), ('p.PNG', 'image/png'), ('p.jpg', 'image/jpeg'),
                                        ('p.svg', 'image/svg+xml'), ('p.gif', 'image/gif')])
def test_local_image_is_embedded(tmp_path, name, mime):
    (tmp_path / name).write_bytes(PNG)
    body, warnings = render(f'<img={name},auto,auto>', base_dir=tmp_path)
    assert f'src="data:{mime};base64,{base64.b64encode(PNG).decode()}"' in body
    assert warnings == []


def test_local_image_in_subfolder_and_absolute_path(tmp_path):
    (tmp_path / '圖 片').mkdir()
    (tmp_path / '圖 片' / 'a.png').write_bytes(PNG)
    # 路徑有空白時用雙引號
    assert 'data:image/png;base64,' in render('<img="圖 片/a.png,10,10">', base_dir=tmp_path)[0]
    assert 'data:image/png;base64,' in render(f'<img="{tmp_path / "圖 片" / "a.png"},10,10">')[0]


def test_missing_image_warns_and_shows_placeholder(tmp_path):
    body, warnings = render('前一行\n<img=images/沒有.png,100,50>', base_dir=tmp_path)
    assert '找不到圖片：images/沒有.png</div>' in body and '<img' not in body
    assert warnings == [(2, '找不到圖片：images/沒有.png')]


def test_relative_path_is_based_on_markdown_folder_not_cwd_or_output(tmp_path):
    source_dir = tmp_path / '講義'
    (source_dir / 'images').mkdir(parents=True)
    (source_dir / 'images' / 'a.png').write_bytes(PNG)
    (source_dir / 'deck.md').write_text('# 圖\n<img=images/a.png,10,10>\n', encoding='utf-8')
    elsewhere = tmp_path / '別的資料夾'
    elsewhere.mkdir()
    (tmp_path / 'out').mkdir()
    result = subprocess.run([sys.executable, '-m', 'briefgen', 'build', '-i', str(source_dir / 'deck.md'),
                             '-o', str(tmp_path / 'out' / 'deck.html')], cwd=elsewhere, capture_output=True)
    assert result.returncode == 0 and result.stderr == b''
    assert 'data:image/png;base64,' in (tmp_path / 'out' / 'deck.html').read_text(encoding='utf-8')


def test_generator_warning_has_file_and_line(tmp_path, capsys):
    source = tmp_path / 'deck.md'
    source.write_text('# 圖\n\n<img=沒有.png,auto,auto>\n', encoding='utf-8')
    gen = PresentationGenerator()
    gen.load_from_markdown(str(source))
    gen.render_html()
    assert capsys.readouterr().err.splitlines() == [f'{source}:3: 找不到圖片：沒有.png']


def test_watch_page_embeds_local_images(tmp_path):
    from briefgen.watch import Watcher
    (tmp_path / 'a.png').write_bytes(PNG)
    source = tmp_path / 'deck.md'
    source.write_text('# 圖\n<img=a.png,10,10>\n', encoding='utf-8')
    watcher = Watcher(source, tmp_path / 'deck.html')
    watcher.check()
    assert 'data:image/png;base64,' in watcher.page()


def test_large_local_image_warns_but_is_embedded(tmp_path):
    (tmp_path / 'big.png').write_bytes(PNG + b'\0' * (1024 * 1024))
    (tmp_path / 'ok.png').write_bytes(PNG + b'\0' * (1024 * 1024 - len(PNG)))
    body, warnings = render('<img=big.png,auto,auto>\n<img=ok.png,auto,auto>', base_dir=tmp_path)
    assert body.count('data:image/png;base64,') == 2
    assert warnings == [(1, '圖片 big.png 有 1.0 MB，嵌入後 HTML 會很大，建議先壓縮')]
