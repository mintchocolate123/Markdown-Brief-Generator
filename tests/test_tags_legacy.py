"""舊語法解析的現有行為（階段三刪除舊解析時一併移除）"""

from briefgen.tags import normalize_color, parse_cell_format, parse_line_format


def test_line_consumes_multiple_tags():
    r = parse_line_format('<size<4>><color<red>><b>文字')
    assert r['text'] == '文字'
    assert r['styles'] == {'font-size': '1.2em', 'color': '#f00', 'font-weight': 'bold'}


def test_line_later_decoration_overrides():
    r = parse_line_format('<u><s>文字')
    assert r['styles'] == {'text-decoration': 'line-through'}


def test_line_consumes_square_brackets():
    assert parse_line_format('[注意]說明')['text'] == '說明'


def test_line_strips_after_tag():
    assert parse_line_format('<b>   文字')['text'] == '文字'


def test_line_link_argument_is_tokenized():
    r = parse_line_format('<link<i>>文字')
    assert r['link'] == 'i'
    assert r['styles'] == {'font-style': 'italic'}


def test_line_block_formats():
    r = parse_line_format('<ct imp cont tab<2> pivot<c>>文字')
    assert (r['is_subtitle'], r['is_important'], r['cont']) == (True, True, True)
    assert (r['indent'], r['align']) == (2, 'center')


def test_cell_consumes_one_tag_and_keeps_space():
    r = parse_cell_format('<b><i> 文字')
    assert r['text'] == '<i> 文字'
    assert r['styles'] == {'font-weight': 'bold'}


def test_cell_ignores_square_brackets():
    assert parse_cell_format('[注意]說明')['text'] == '[注意]說明'


def test_cell_imp():
    assert parse_cell_format('<imp>標題') == {'text': '標題', 'imp': True, 'styles': {}}


def test_normalize_color():
    assert normalize_color(' Purple ') == '#800080'
    assert normalize_color('#123') == '#123'
