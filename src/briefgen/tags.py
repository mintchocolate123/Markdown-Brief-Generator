#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tags.py - 行首格式標記解析（行內文字、表格儲存格、樹節點共用）
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple


SIZE_MAP = {
    '1': '0.7em', '2': '0.85em', '3': '1em',
    '4': '1.2em', '5': '1.5em', '6': '2em', '7': '2.5em'
}

PIVOT_MAP = {'l': 'left', 'c': 'center', 'r': 'right'}

COLOR_MAP = {
    'black': '#000', 'white': '#fff',
    'red': '#f00', 'green': '#008000', 'blue': '#00f',
    'yellow': '#ff0', 'cyan': '#0ff',
    'orange': '#ffa500', 'purple': '#800080',
    'pink': '#ffc0cb', 'gray': '#808080',
}


def normalize_color(color: str) -> str:
    """標準化顏色值"""
    return COLOR_MAP.get(color.strip().lower(), color)


def split_tokens_regex(fmt: str) -> List[str]:
    """以角括號與空白切割（行內文字）"""
    return [t for t in re.split(r'[<>\s]+', fmt) if t]


def split_tokens_whitespace(fmt: str) -> List[str]:
    """只以空白切割（儲存格、樹節點）"""
    return fmt.split()


def find_tag_end(text: str) -> int:
    """找到開頭標記對應的結束位置，找不到時回傳 -1"""
    start_char = text[0]
    end_char = '>' if start_char == '<' else ']'
    depth = 0
    for i, c in enumerate(text):
        if c == start_char:
            depth += 1
        elif c == end_char:
            depth -= 1
            if depth == 0:
                return i
    return -1


def new_result(text: str) -> Dict[str, Any]:
    return {
        'text': text,
        'cont': False,
        'is_subtitle': False,
        'is_important': False,
        'indent': 0,
        'align': None,
        'link': None,
        'image': None,
        'styles': {},
    }


def apply_format(fmt: str, tokens: List[str], result: Dict[str, Any]) -> None:
    """應用單個格式標記到結果"""
    if 'cont' in tokens:
        result['cont'] = True

    if 'ct' in tokens:
        result['is_subtitle'] = True

    if 'imp' in tokens:
        result['is_important'] = True

    tab_match = re.search(r'tab<(\d+)>', fmt)
    if tab_match:
        result['indent'] = int(tab_match.group(1))

    pivot_match = re.search(r'pivot<([lcr])>', fmt)
    if pivot_match:
        result['align'] = PIVOT_MAP.get(pivot_match.group(1))

    link_match = re.search(r'link<([^>]+)>', fmt)
    if link_match:
        result['link'] = link_match.group(1)

    img_match = re.search(r'img<([^,]+),([^,]+),([^>]+)>', fmt)
    if img_match:
        result['image'] = {
            'url': img_match.group(1),
            'width': img_match.group(2),
            'height': img_match.group(3),
        }

    size_match = re.search(r'size<(\d)>', fmt)
    if size_match and size_match.group(1) in SIZE_MAP:
        result['styles']['font-size'] = SIZE_MAP[size_match.group(1)]

    color_match = re.search(r'color<([^>]+)>', fmt)
    if color_match:
        result['styles']['color'] = normalize_color(color_match.group(1))

    if 'b' in tokens or 'bold' in tokens:
        result['styles']['font-weight'] = 'bold'

    if 'i' in tokens or 'italic' in tokens:
        result['styles']['font-style'] = 'italic'

    underline = 'u' in tokens or 'underline' in tokens
    strike = 's' in tokens or 'strike' in tokens

    if underline and strike:
        result['styles']['text-decoration'] = 'underline line-through'
    elif underline:
        result['styles']['text-decoration'] = 'underline'
    elif strike:
        result['styles']['text-decoration'] = 'line-through'


def parse_tags(
    text: str,
    *,
    openers: str,
    multi: bool,
    strip: bool,
    tokenize: Callable[[str], List[str]],
) -> Dict[str, Any]:
    """
    解析開頭的格式標記

    openers: 可作為標記開頭的字元
    multi: 是否連續解析多個標記
    strip: 標記後的剩餘文字是否 strip（未解析到標記時也回傳 strip 後的文字）
    tokenize: 切割標記內容的方式
    """
    result = new_result(text)

    stripped = text.strip()
    if not stripped:
        return result

    rest = stripped
    consumed = False
    while rest and rest[0] in openers:
        end = find_tag_end(rest)
        if end == -1:
            break

        fmt = rest[1:end]
        rest = rest[end+1:]
        if strip:
            rest = rest.strip()
        apply_format(fmt, tokenize(fmt), result)
        consumed = True

        if not multi:
            break

    if consumed or strip:
        result['text'] = rest
    return result


def parse_line_format(line: str) -> Dict[str, Any]:
    """解析行內文字的格式標記"""
    return parse_tags(line, openers='<[', multi=True, strip=True,
                      tokenize=split_tokens_regex)


def parse_cell_format(text: str) -> Dict[str, Any]:
    """解析表格儲存格與樹節點文字的格式標記"""
    parsed = parse_tags(text, openers='<', multi=False, strip=False,
                        tokenize=split_tokens_whitespace)
    return {
        'text': parsed['text'],
        'imp': parsed['is_important'],
        'styles': parsed['styles'],
    }


# ---------------------------------------------------------------------------
# 新語法：行首一個 <...>，空白分隔 name 或 name=value（規格見 CLAUDE.md）
# ---------------------------------------------------------------------------

FLAG_FORMATS = {
    'b': 'bold', 'bold': 'bold',
    'i': 'italic', 'italic': 'italic',
    'u': 'underline', 'underline': 'underline',
    's': 'strike', 'strike': 'strike',
    'ct': 'ct', 'imp': 'imp', 'cont': 'cont',
}

VALUE_FORMATS = {
    'tab': lambda v: re.fullmatch(r'\d+', v) is not None,
    'pivot': lambda v: v in PIVOT_MAP,
    'size': lambda v: v in SIZE_MAP,
    'color': lambda v: v != '',
    'link': lambda v: v != '',
    'img': lambda v: len(v.split(',')) == 3 and all(p.strip() for p in v.split(',')),
}


def split_top_level(text: str) -> List[str]:
    """以空白切割，雙引號內不切"""
    tokens = []
    current = ''
    in_quote = False
    for c in text:
        if c == '"':
            in_quote = not in_quote
        elif c.isspace() and not in_quote:
            if current:
                tokens.append(current)
            current = ''
            continue
        current += c
    if current:
        tokens.append(current)
    return tokens


def split_token(token: str) -> Tuple[str, Optional[str]]:
    """name 或 name=value（只切第一個 =，去掉值外層的雙引號）"""
    name, sep, value = token.partition('=')
    if not sep:
        return name, None
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return name, value


def find_closing(text: str) -> int:
    """找到雙引號外的第一個 >，找不到時回傳 -1"""
    in_quote = False
    for i, c in enumerate(text):
        if c == '"':
            in_quote = not in_quote
        elif c == '>' and not in_quote:
            return i
    return -1


def token_error(name: str, value: Optional[str]) -> Optional[str]:
    """檢查單一格式，合法時回傳 None"""
    if name in FLAG_FORMATS:
        return None if value is None else f'格式 {name} 不接受參數'
    if name in VALUE_FORMATS:
        if value is None:
            return f'格式 {name} 需要參數'
        return None if VALUE_FORMATS[name](value) else f'格式 {name} 的值不合法：{value}'
    return f'未知的格式名稱：{name}'


def parse_format(line: str) -> Dict[str, Any]:
    """
    解析行首格式（行內文字、表格儲存格、樹節點共用）

    回傳 new_result() 的欄位，另加 warnings（訊息列表，不含行號）。
    cont 行的剩餘文字不 strip。
    """
    result = new_result(line.strip())
    result['warnings'] = []
    text = result['text']

    if text.startswith('\\<'):
        result['text'] = text[1:]
        return result
    if not text.startswith('<'):
        return result

    end = find_closing(text)
    if end == -1:
        tokens = split_top_level(text[1:])
        if tokens and split_token(tokens[0])[0] in FLAG_FORMATS.keys() | VALUE_FORMATS.keys():
            result['warnings'].append('行首格式缺少結尾的 >，整行視為文字')
        return result

    tokens = split_top_level(text[1:end])
    if not tokens:
        result['warnings'].append('空的 <>，整行視為文字')
        return result

    parsed = [split_token(token) for token in tokens]
    for name, value in parsed:
        error = token_error(name, value)
        if error:
            result['warnings'].append(f'{error}，整行視為文字')
            return result

    decorations = set()
    for name, value in parsed:
        kind = FLAG_FORMATS.get(name, name)
        if kind == 'bold':
            result['styles']['font-weight'] = 'bold'
        elif kind == 'italic':
            result['styles']['font-style'] = 'italic'
        elif kind in ('underline', 'strike'):
            decorations.add(kind)
            result['styles']['text-decoration'] = None
        elif kind == 'ct':
            result['is_subtitle'] = True
        elif kind == 'imp':
            result['is_important'] = True
        elif kind == 'cont':
            result['cont'] = True
        elif kind == 'tab':
            result['indent'] = int(value)
        elif kind == 'pivot':
            result['align'] = PIVOT_MAP[value]
        elif kind == 'size':
            result['styles']['font-size'] = SIZE_MAP[value]
        elif kind == 'color':
            result['styles']['color'] = normalize_color(value)
        elif kind == 'link':
            result['link'] = value
        elif kind == 'img':
            url, width, height = value.split(',')
            result['image'] = {'url': url, 'width': width, 'height': height}

    if decorations:
        result['styles']['text-decoration'] = ' '.join(
            css for kind, css in (('underline', 'underline'), ('strike', 'line-through'))
            if kind in decorations
        )

    rest = text[end+1:]
    if not result['cont']:
        rest = rest.strip()
    if re.match(r'\s*<[^>]*>', rest):
        result['warnings'].append('格式後面的 <...> 會顯示為文字，可能是舊語法（一行只能有一個 <...>）')
    result['text'] = rest
    return result
