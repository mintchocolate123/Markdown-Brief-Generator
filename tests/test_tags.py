"""新語法 parse_format 的單元測試"""

import pytest

from briefgen.tags import COLOR_MAP, normalize_color, parse_format, split_list_item


def fmt(line):
    return parse_format(line)


@pytest.mark.parametrize('line, styles', [
    ('<b>x', {'font-weight': 'bold'}),
    ('<bold>x', {'font-weight': 'bold'}),
    ('<i>x', {'font-style': 'italic'}),
    ('<italic>x', {'font-style': 'italic'}),
    ('<u>x', {'text-decoration': 'underline'}),
    ('<underline>x', {'text-decoration': 'underline'}),
    ('<s>x', {'text-decoration': 'line-through'}),
    ('<strike>x', {'text-decoration': 'line-through'}),
    ('<u s>x', {'text-decoration': 'underline line-through'}),
    ('<s u>x', {'text-decoration': 'underline line-through'}),
    ('<size=1>x', {'font-size': '0.7em'}),
    ('<size=7>x', {'font-size': '2.5em'}),
    ('<color=purple>x', {'color': '#d79eff'}),
    ('<color=#ff6b6b>x', {'color': '#ff6b6b'}),
    ('<b size=4 color=red>x', {'font-weight': 'bold', 'font-size': '1.2em', 'color': '#ff9999'}),
])
def test_text_styles(line, styles):
    r = fmt(line)
    assert (r['text'], r['styles'], r['warnings']) == ('x', styles, [])


def test_ct_imp():
    r = fmt('<ct imp>x')
    assert (r['is_subtitle'], r['is_important']) == (True, True)


@pytest.mark.parametrize('value, align', [('l', 'left'), ('c', 'center'), ('r', 'right')])
def test_pivot(value, align):
    assert fmt(f'<pivot={value}>x')['align'] == align


def test_tab():
    assert fmt('<tab=3>x')['indent'] == 3


def test_link_splits_only_first_equals():
    assert fmt('<link=https://a.com/?x=1&y=2>x')['link'] == 'https://a.com/?x=1&y=2'


def test_img():
    r = fmt('<img=https://a.com/a.png,300,150>')
    assert r['image'] == {'url': 'https://a.com/a.png', 'width': '300', 'height': '150'}


def test_later_duplicate_overrides():
    r = fmt('<color=red color=blue>x')
    assert (r['styles'], r['warnings']) == ({'color': '#adadff'}, [])


def test_whitespace_after_tag_is_stripped():
    assert fmt('<b>   x  ')['text'] == 'x'


def test_leading_whitespace_before_tag():
    assert fmt('   <b>x')['styles'] == {'font-weight': 'bold'}


def test_plain_text():
    r = fmt('  普通文字 ')
    assert (r['text'], r['styles'], r['warnings']) == ('普通文字', {}, [])


# --- cont -------------------------------------------------------------------

def test_cont_keeps_whitespace_after_tag():
    r = fmt('<cont b> word')
    assert (r['cont'], r['text'], r['styles']) == (True, ' word', {'font-weight': 'bold'})


# --- 引號 --------------------------------------------------------------------

def test_quoted_value_with_spaces():
    r = fmt('<color="rgb(255, 0, 0)" b>x')
    assert r['styles'] == {'color': 'rgb(255, 0, 0)', 'font-weight': 'bold'}
    assert r['text'] == 'x'


def test_quoted_value_may_contain_closing_bracket():
    r = fmt('<link="https://a.com/?q=>">x')
    assert (r['link'], r['text']) == ('https://a.com/?q=>', 'x')


def test_unclosed_quote_means_no_closing_bracket():
    r = fmt('<color="red>x')
    assert r['text'] == '<color="red>x'
    assert r['warnings'] == ['行首格式缺少結尾的 >，整行視為文字']


# --- 未知名稱與不合法的值 ------------------------------------------------------

@pytest.mark.parametrize('line, warning', [
    ('<foo>x', '未知的格式名稱：foo'),
    ('<b foo>x', '未知的格式名稱：foo'),
    ('<B>x', '未知的格式名稱：B'),
    ('<bolder>x', '未知的格式名稱：bolder'),
    ('<size<5>>x', '未知的格式名稱：size<5'),
    ('<size=0>x', '格式 size 的值不合法：0'),
    ('<size=9>x', '格式 size 的值不合法：9'),
    ('<pivot=x>x', '格式 pivot 的值不合法：x'),
    ('<tab=abc>x', '格式 tab 的值不合法：abc'),
    ('<img=a.png,1>x', '格式 img 的值不合法：a.png,1'),
    ('<b=1>x', '格式 b 不接受參數'),
    ('<color>x', '格式 color 需要參數'),
    ('<color=>x', '格式 color 的值不合法：'),
])
def test_invalid_line_is_plain_text(line, warning):
    r = fmt(line)
    assert (r['text'], r['styles'], r['link']) == (line, {}, None)
    assert r['warnings'] == [f'{warning}，整行視為文字']


def test_missing_closing_bracket_warns_when_first_name_is_known():
    r = fmt('<b 粗體')
    assert (r['text'], r['styles']) == ('<b 粗體', {})
    assert r['warnings'] == ['行首格式缺少結尾的 >，整行視為文字']


def test_missing_closing_bracket_without_known_name_is_silent():
    assert fmt('<3 我愛你')['warnings'] == []


def test_empty_tag():
    r = fmt('<>x')
    assert (r['text'], r['warnings']) == ('<>x', ['空的 <>，整行視為文字'])
    assert fmt('<  >x')['warnings'] == ['空的 <>，整行視為文字']


def test_second_tag_is_literal_text_with_warning():
    r = fmt('<b><i>x')
    assert (r['text'], r['styles']) == ('<i>x', {'font-weight': 'bold'})
    assert r['warnings'] == ['格式後面的 <...> 會顯示為文字，可能是舊語法（一行只能有一個 <...>）']


# --- 跳脫 --------------------------------------------------------------------

def test_escaped_bracket_is_literal():
    r = fmt('\\<b>不是格式')
    assert (r['text'], r['styles'], r['warnings']) == ('<b>不是格式', {}, [])


def test_escape_after_leading_whitespace():
    assert fmt('  \\<html>')['text'] == '<html>'


def test_backslash_elsewhere_is_kept():
    assert fmt('a\\<b')['text'] == 'a\\<b'


# --- 顏色 --------------------------------------------------------------------

def test_normalize_color():
    assert normalize_color(' Purple ') == '#d79eff'
    assert normalize_color('#123') == '#123'



# --- 清單 --------------------------------------------------------------------

@pytest.mark.parametrize('line, expected', [
    ('- 項目', (0, '項目')),
    ('  - 項目', (1, '項目')),
    ('    - 項目', (2, '項目')),
    ('   - 項目', (1, '項目')),
    ('\t- 項目', (1, '項目')),
    ('\t\t- 項目', (2, '項目')),
    ('\t  - 項目', (2, '項目')),
    ('- <b>項目', (0, '<b>項目')),
    ('- ', (0, '')),
])
def test_list_item(line, expected):
    assert split_list_item(line) == expected


@pytest.mark.parametrize('line', ['-項目', '---', '-- 項目', '\\- 項目', '項目 - 不是', '-\t項目'])
def test_not_list_item(line):
    assert split_list_item(line) is None


# 卡片背景（10% 白疊在頁面漸層上）的相對亮度範圍
CARD_LUMINANCE = (0.0324, 0.0627)


def _luminance(hex_color):
    h = hex_color.lstrip('#')
    h = ''.join(c * 2 for c in h) if len(h) == 3 else h
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


@pytest.mark.parametrize('name', sorted(set(COLOR_MAP) - {'black'}))
def test_color_names_meet_wcag_aa_on_card(name):
    text = _luminance(COLOR_MAP[name])
    worst = min((max(text, bg) + 0.05) / (min(text, bg) + 0.05) for bg in CARD_LUMINANCE)
    assert worst >= 4.5, f'{name} {COLOR_MAP[name]} 對比 {worst:.2f}'
