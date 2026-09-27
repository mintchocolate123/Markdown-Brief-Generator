#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tags.py - 行首格式標記解析（行內文字、表格儲存格、樹節點共用）

行首一個 <...>，空白分隔 name 或 name=value，規格見 CLAUDE.md
"""

import re
from typing import Any, Dict, List, Optional, Tuple


SIZE_MAP = {
    '1': '0.7em', '2': '0.85em', '3': '1em',
    '4': '1.2em', '5': '1.5em', '6': '2em', '7': '2.5em'
}

PIVOT_MAP = {'l': 'left', 'c': 'center', 'r': 'right'}

# 顏色名稱已針對深色卡片背景調亮，除 black 外對比至少 4.5:1（WCAG AA）；
# black 在卡片上看不清楚，維持 #000。自訂色碼不調整。
COLOR_MAP = {
    'black': '#000', 'white': '#fff',
    'red': '#ff9999', 'green': '#00d200', 'blue': '#adadff',
    'yellow': '#ff0', 'cyan': '#0ff',
    'orange': '#ffa500', 'purple': '#d79eff',
    'pink': '#ffc0cb', 'gray': '#b6b6b6',
}


def normalize_color(color: str) -> str:
    """標準化顏色值"""
    return COLOR_MAP.get(color.strip().lower(), color)


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
        'formats': [],
        'warnings': [],
    }


FLAG_FORMATS = {
    'b': 'bold', 'bold': 'bold',
    'i': 'italic', 'italic': 'italic',
    'u': 'underline', 'underline': 'underline',
    's': 'strike', 'strike': 'strike',
    'ct': 'ct', 'imp': 'imp', 'cont': 'cont',
}

# 只作用於整行的格式，不能用在 cont 行
BLOCK_FORMATS = ('pivot', 'tab', 'imp', 'ct', 'img')

def _valid_image(value: str) -> bool:
    """img=網址或路徑,寬,高；寬高為整數（像素）或 auto"""
    parts = [p.strip() for p in value.split(',')]
    return (len(parts) == 3 and parts[0] != ''
            and all(re.fullmatch(r'\d+|auto', p) for p in parts[1:]))


VALUE_FORMATS = {
    'tab': lambda v: re.fullmatch(r'\d+', v) is not None,
    'pivot': lambda v: v in PIVOT_MAP,
    'size': lambda v: v in SIZE_MAP,
    'color': lambda v: v != '',
    'link': lambda v: v != '',
    'img': lambda v: _valid_image(v),
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


LIST_ITEM_RE = re.compile(r'^([ \t]*)- (.*)$')


def split_list_item(line: str) -> Optional[Tuple[int, str]]:
    """行首 "- " 為清單項目，回傳 (層級, 剩餘文字)；每 2 個空白或 1 個 Tab 多一層"""
    match = LIST_ITEM_RE.match(line)
    if not match:
        return None
    indent = match.group(1)
    return indent.count('\t') + indent.count(' ') // 2, match.group(2)


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

    result['formats'] = [name for name, _ in parsed]
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
            url, width, height = (p.strip() for p in value.split(','))
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
